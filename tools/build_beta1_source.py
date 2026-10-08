#!/usr/bin/env python3
"""Build the curated source archive. Normal mode requires committed release files."""
import argparse
from datetime import datetime,timezone
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parents[1]


def git(*args):
    r=subprocess.run(['git','--no-pager','-C',str(ROOT),*args],capture_output=True,text=True,env={**os.environ,"GIT_OPTIONAL_LOCKS":"0"})
    return r.returncode,r.stdout.strip()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',action='store_true',help='Build an explicitly labelled uncommitted review candidate')
    parser.add_argument('--output-dir',type=Path,default=Path.home()/'Downloads')
    args=parser.parse_args()
    manifest=json.loads((ROOT/'release/beta1-files.json').read_text())
    paths=manifest['files'];version=manifest['version']
    rc,head=git('rev-parse','HEAD')
    if not args.candidate:
        rc_top,top=git('rev-parse','--show-toplevel')
        if rc or rc_top or Path(top).resolve()!=ROOT:
            raise SystemExit('Build a final archive from the committed repository, or use --candidate for review.')
        rc_status,status=git('status','--porcelain','--untracked-files=all','--',*paths)
        rc_tracked,tracked=git('ls-files','--',*paths)
        if rc_status or rc_tracked or status or set(tracked.splitlines())!=set(paths):
            raise SystemExit('Release files must all be tracked and committed. Unrelated work can remain local.')
    data={};hashes={}
    for name in paths:
        path=ROOT/name
        if Path(name).is_absolute() or '..' in Path(name).parts or not path.resolve().is_relative_to(ROOT):
            raise SystemExit('Invalid release path: '+name)
        if any(p.is_symlink() for p in (path,*path.parents) if p!=ROOT) or not path.is_file():
            raise SystemExit('Missing or linked release file: '+name)
        content=path.read_bytes()
        if name.endswith('.py'):compile(content,name,'exec')
        data[name]=content;hashes[name]=hashlib.sha256(content).hexdigest()
    metadata=dict(version=version,candidate=args.candidate,commit=head if not rc else None,sha256=hashes)
    data['RELEASE_BUILD.json']=json.dumps(metadata,indent=2).encode()
    destination=args.output_dir.expanduser().resolve()
    if not destination.is_dir():raise SystemExit('Output directory must exist.')
    suffix='-candidate-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') if args.candidate else '-source'
    stem='hvacgooee-'+version
    output=destination/(stem+suffix+'.tar.gz')
    with output.open('xb') as stream,tarfile.open(fileobj=stream,mode='w:gz') as tar:
        for name,content in sorted(data.items()):
            info=tarfile.TarInfo(stem+'/'+name);info.size=len(content);info.mode=0o644
            tar.addfile(info,io.BytesIO(content))
    checksum=hashlib.sha256(output.read_bytes()).hexdigest()
    checksum_path=output.with_name(output.name+'.sha256')
    with checksum_path.open('x') as stream:stream.write(checksum+'  '+output.name+'\n')
    print('Created:',output);print('SHA256:',checksum)
    print('No tag, push or upload performed.')


if __name__=='__main__':main()
