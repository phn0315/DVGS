"""Build a GitHub-ready gallery from the four original split-screen videos.
Dependencies: Python 3.8+, opencv-python, numpy, Pillow; FFmpeg on PATH.
Frames are cropped from decoded video pixels, never enhanced or synthesized.
"""
from pathlib import Path
import argparse, json, math, shutil, subprocess, csv, html
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

VIDEO_LINKS={'imaging_0706': 'https://www.bilibili.com/video/BV13Ceu6eE2b/', 'imaging_0718': 'https://www.bilibili.com/video/BV1Gkeu6NEkB/', 'vslam_0718': 'https://www.bilibili.com/video/BV1Xkeu6NE8e/', 'vslam_0706': 'https://www.bilibili.com/video/BV1akeu6NEtk/'}

SPECS=[
 ('imaging_0706','imaging','0706_123_1.5x_split_screen.mp4',['0706_1','0706_2','0706_3']),
 ('imaging_0718','imaging','0718_123_split_screen.mp4',['0718_1','0718_2','0718_3']),
 ('vslam_0718','vslam','0718_123_ORB_incremental_VSLAM_six_way_strict_sync.mp4',['VSLAM-11','VSLAM-22','VSLAM-33']),
 ('vslam_0706','vslam','0706_456_ORB_incremental_VSLAM_66_video2_strict_sync.mp4',['VSLAM-44','VSLAM-55','VSLAM-66'])]

def write_png(path,frame):
 path.parent.mkdir(parents=True,exist_ok=True)
 ok,data=cv2.imencode('.png',frame)
 if not ok:raise RuntimeError('PNG encode failed')
 data.tofile(str(path))

def quality(frame,row):
 # Exclude labels, borders, and the depth colors/ORB colored overlays.
 y=row*360
 roi=frame[y+25:y+250,248:952]
 gray=cv2.cvtColor(roi,cv2.COLOR_BGR2GRAY)
 mask=(gray>18)&(gray<245)&((roi.max(axis=2).astype(int)-roi.min(axis=2))<24)
 mask=cv2.erode(mask.astype('uint8'),np.ones((3,3),np.uint8))>0
 if mask.sum()<1000:return -1.
 lap=cv2.Laplacian(gray,cv2.CV_32F)
 # Texture-based ranking within the same dataset, not an image-quality metric.
 return float(np.var(lap[mask])*math.sqrt(mask.mean()))

def select_frames(src,group,kind,labels,dst):
 cap=cv2.VideoCapture(str(src))
 if not cap.isOpened():raise RuntimeError('Cannot open '+str(src))
 fps=cap.get(cv2.CAP_PROP_FPS);count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
 if (int(cap.get(3)),int(cap.get(4)))!=(1920,1080):raise ValueError('Expected the supplied 1920x1080 layout')
 # Six separate temporal intervals, with small margins at each boundary.
 edges=np.linspace(.04*count,.97*count,7)
 targets={}
 for b in range(6):
  lo,hi=edges[b],edges[b+1];margin=(hi-lo)*.09
  for ix in np.linspace(lo+margin,hi-margin,24).astype(int):targets[int(ix)]=b
 best={};idx=0
 while idx<count:
  ok=cap.grab()
  if not ok:break
  if idx in targets:
   ok,frame=cap.retrieve()
   if ok:
    for row in range(3):
     score=quality(frame,row);key=(row,targets[idx])
     if key not in best or score>best[key][0]:best[key]=(score,idx,frame[row*360:(row+1)*360,240:1680].copy())
  idx+=1
 cap.release()
 if len(best)!=18:raise RuntimeError('Incomplete extraction for '+group)
 records=[]
 for row,label in enumerate(labels):
  # Common vertical crop per dataset, preserving all visible content in its six selected frames.
  top,bottom=2,358
  if kind=='imaging':
   ys=[]
   for b in range(6):
    im=best[row,b][2]
    occupied=(im[2:358].max(axis=2)>18).sum(axis=1)>8
    yy=np.where(occupied)[0]+2
    if len(yy):ys.extend([int(yy.min()),int(yy.max())+1])
   if ys:top=max(2,min(ys)-10);bottom=min(358,max(ys)+10)
  for b in range(6):
   score,ix,im=best[row,b];rel=Path('.work/frames')/group/label/('frame_%02d.png'%(b+1))
   write_png(dst/rel,im[top:bottom])
   records.append(dict(group=group,kind=kind,dataset=label,sample=b+1,source=src.name,frame_index=ix,video_seconds=round(ix/fps,3),selection_score=round(score,4),crop_xywh=[240,row*360+top,1440,bottom-top],image=rel.as_posix()))
 cap=cv2.VideoCapture(str(src));cap.set(cv2.CAP_PROP_POS_FRAMES,int(count*.5));ok,poster=cap.read();cap.release()
 if ok:write_png(dst/'assets/posters'/f'{group}.png',poster)
 return records,dict(group=group,source=src.name,fps=fps,frames=count,duration=count/fps,kind=kind,labels=labels)

def build_pages(dst,records,meta):
 try:font=ImageFont.truetype('arial.ttf',30)
 except OSError:font=ImageFont.load_default()
 md=['# DVGS: Intensity–Depth Imaging and Visual SLAM','',
 'Each complete video is followed by three datasets. Each dataset is summarized in one **2-column × 3-row montage**, containing six time-separated paired views. Click a montage for full resolution.','',
 '[中文使用说明](UPLOAD_GUIDE_CN.md) · [Interactive gallery](index.html)','',
 'The figures are direct crops from the supplied videos; no AI enhancement or geometric alteration is applied. All times below refer to the supplied video timeline, not raw sensor timestamps.','']
 page=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DVGS Results</title><style>body{background:#f7f9fc;color:#17212b;font:16px/1.7 system-ui;margin:0}main{max-width:1300px;margin:auto;padding:30px}h1{font-size:36px}h2{border-bottom:2px solid #d1d9e0;padding-top:30px}figure{margin:24px 0;background:white;border:1px solid #d1d9e0;border-radius:8px;padding:12px}img,video{width:100%;display:block}video{max-height:680px;background:black}figcaption{padding:12px 0;color:#465568}a{color:#0969da}</style><main><h1>DVGS: Intensity–Depth Imaging and Visual SLAM</h1><p>Six selected paired frames per dataset. Click figures to inspect their native-resolution montage. Video timestamps refer to the supplied display timeline.</p>']
 gallery=[]
 for kind,title in [('imaging','1. Intensity–depth imaging'),('vslam','2. Visual SLAM and incremental mapping')]:
  md+=['## '+title,''];page+=['<h2>'+title+'</h2>']
  for g in [x for x in meta if x['kind']==kind]:
   group=g['group'];video=VIDEO_LINKS[group];poster=f'assets/posters/{group}.png';title2=('0706' if '0706' in group else '0718')+' sequences'
   md+=['### '+title2,'',f'[![Complete video: {title2}]({poster})]({video})','',f'**[Watch the complete video on Bilibili]({video})** · {g["duration"]:.2f} s','']
   page += ['<h3>'+title2+'</h3>',f'<a href="{video}" target="_blank" rel="noopener noreferrer"><img src="{poster}" alt="Watch on Bilibili"></a><p><a href="{video}">Watch the complete video on Bilibili</a></p>']
   for label in g['labels']:
    rr=[r for r in records if r['group']==group and r['dataset']==label]
    ims=[Image.open(dst/r['image']).convert('RGB') for r in rr]
    w=max(im.width for im in ims);h=max(im.height for im in ims);pad=18;captionh=54
    montage=Image.new('RGB',(2*w+3*pad,3*(h+captionh)+4*pad),'white');draw=ImageDraw.Draw(montage)
    for i,(r,im) in enumerate(zip(rr,ims)):
     x=pad+(i%2)*(w+pad);y=pad+(i//2)*(h+captionh+pad)
     montage.paste(im,(x,y));draw.text((x+8,y+h+9),f'({chr(97+i)}) {label} | video {r["video_seconds"]:.2f} s',font=font,fill='#263648')
    rel=f'assets/montages/{group}_{label}.jpg';(dst/rel).parent.mkdir(parents=True,exist_ok=True);montage.save(dst/rel,quality=94,subsampling=0,optimize=True)
    caption=('Each pair: relative return intensity (left) and co-registered pseudo-colored radial depth (right). Building contours and surface boundaries can be compared at the six selected viewpoints.' if kind=='imaging' else 'Each pair: ORB features on the intensity image (left) and the source video\'s incremental point cloud with trajectory (right). The six views show feature observations and successive mapping states.')
    times='; '.join(f'({chr(97+i)}) {r["video_seconds"]:.2f} s' for i,r in enumerate(rr))
    md+=['#### '+label,'',f'[![{label}: six paired views]({rel})]({rel})','',caption+' **Video times:** '+times+'.','']
    page += ['<h3>'+label+'</h3>',f'<figure><a href="{rel}"><img loading="lazy" src="{rel}" alt="{label}: six paired views"></a><figcaption>{html.escape(caption)}<br>{times}</figcaption></figure>']
    gallery.append(dict(group=group,dataset=label,montage=rel,size=montage.size,times=[r['video_seconds'] for r in rr]))
 md+=['## Selection and provenance','',
 'Six separate intervals cover 4–97% of each supplied video. In each interval, 24 candidates are ranked using a masked Laplacian sharpness score on the grayscale intensity panel. Scoring excludes labels, borders, and colored feature markers. This is a selection heuristic, not a quantitative imaging-quality result.','',
 'Paired panels always come from the same decoded frame. The montage preserves the extracted pixel dimensions; it only removes side labels/empty margins and adds captions. High-quality JPEG is used to reduce download size. The original video retains its original labels.','',
 'The VSLAM identifiers are copied from the videos and are not assumed to match imaging row indices. Source video playback/synchronization factors are unchanged; playback speed is not a runtime benchmark. Complete videos are hosted externally on Bilibili; this repository contains no video files.','',
 'See `selection_manifest.csv` for source filenames, frame indices, video times and crop coordinates. See `gallery_manifest.json` for the 12 montage files. Visual selections do not establish trajectory accuracy or replace full-sequence evaluation.','',
 '## Rebuild','', '```bash','pip install -r requirements.txt','python generate_showcase.py --source-dir /path/to/original/videos --output . --skip-video','```','',
 'On Windows, `build.bat` provides the same workflow. The four original files are required. This external-video edition generates images and Bilibili links only; it does not copy or encode video files.']
 page+=['<p>Direct video-frame crops; no AI reconstruction. Selections are qualitative illustrations. Consult the CSV manifest for provenance.</p></main></html>']
 (dst/'README.md').write_text('\n'.join(md),encoding='utf8');(dst/'index.html').write_text('\n'.join(page),encoding='utf8');(dst/'.nojekyll').write_text('');(dst/'gallery_manifest.json').write_text(json.dumps(gallery,indent=2),encoding='utf8')

def main():
 a=argparse.ArgumentParser();a.add_argument('--source-dir',type=Path,required=True);a.add_argument('--output',type=Path,default=Path('github'));a.add_argument('--ffmpeg',default='ffmpeg');a.add_argument('--encoder',default='libx264',choices=['libx264','h264_nvenc']);a.add_argument('--reuse-frames',action='store_true');a.add_argument('--skip-video',action='store_true');args=a.parse_args();dst=args.output.resolve();dst.mkdir(parents=True,exist_ok=True)
 records=[];meta=[]
 if args.reuse_frames:
  records=json.loads((dst/'selection_manifest.json').read_text());meta=json.loads((dst/'videos.json').read_text())
 else:
  for group,kind,name,labels in SPECS:
   print('Selecting '+group,flush=True);rr,mm=select_frames(args.source_dir/name,group,kind,labels,dst);records+=rr;meta.append(mm)
  (dst/'selection_manifest.json').write_text(json.dumps(records,indent=2),encoding='utf8');(dst/'videos.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
  with (dst/'selection_manifest.csv').open('w',newline='',encoding='utf-8-sig') as f:
   w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
 if False:  # External-video edition: never create local video files.
  (dst/'assets/videos').mkdir(parents=True,exist_ok=True)
  for g in meta:
   target=dst/'assets/videos'/f'{g["group"]}.mp4'
   if target.exists() and target.stat().st_size>1000:continue
   print('Encoding '+g['group'],flush=True)
   enc=['-c:v','libx264','-preset','fast','-crf','23'] if args.encoder=='libx264' else ['-c:v','h264_nvenc','-b:v','6M']
   cmd=[args.ffmpeg,'-y','-i',str(args.source_dir/g['source']),'-map','0:v:0','-map','0:a?','-vf','fps=30']+enc+['-maxrate','10M','-bufsize','20M','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',str(target)]
   log=dst/(g['group']+'_encode.log')
   with log.open('w') as f:subprocess.run(cmd,stdout=f,stderr=f,check=True)
   if target.stat().st_size>=95*1024*1024:raise RuntimeError('Video exceeds repository target size: '+str(target))
 build_pages(dst,records,meta)
 print('DONE: '+str(dst),flush=True)

if __name__=='__main__':main()
