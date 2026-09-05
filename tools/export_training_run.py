"""Export a complete or interrupted run without omitting checkpoints or logs."""
import argparse,hashlib,json,zipfile
from pathlib import Path


def export(run,destination):
    run=run.resolve();destination=destination.resolve()
    if destination.is_relative_to(run):raise ValueError('Export must be outside the run directory')
    files=sorted(p for p in run.rglob('*') if p.is_file())
    if not files:raise ValueError('Empty run')
    members=[]
    for p in files:
        if p.is_symlink():raise ValueError('Symlinks not permitted in export')
        members.append({'path':p.relative_to(run).as_posix(),'bytes':p.stat().st_size,
                        'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    manifest={'format':'gppo-training-export/1.0.0','source_directory':str(run),
        'completed':(run/'results.json').is_file(),'contains_failure':(run/'failure.json').is_file(),
        'checkpoint_count':sum(p.suffix=='.pt' for p in files),'files':members}
    with zipfile.ZipFile(destination,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for p,member in zip(files,members):archive.write(p,member['path'])
        archive.writestr('EXPORT-MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    with zipfile.ZipFile(destination) as archive:
        for member in members:
            value=archive.read(member['path'])
            if len(value)!=member['bytes'] or hashlib.sha256(value).hexdigest()!=member['sha256']:
                raise ValueError('Archive readback mismatch')
    result={'path':str(destination),'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
            'bytes':destination.stat().st_size,'verified_members':len(members),'checkpoint_count':manifest['checkpoint_count'],
            'completed':manifest['completed']}
    destination.with_suffix(destination.suffix+'.sha256.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(export(args.run,args.output)))
