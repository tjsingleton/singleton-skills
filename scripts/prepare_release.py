#!/usr/bin/env python3
"""Prepare an identifiable, unpublished package from one committed revision."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def prepare(output: Path, revision: str) -> None:
    def git(*args: str) -> bytes:
        return subprocess.check_output(['git', '-C', str(ROOT), *args])

    source = git('rev-parse', '--verify', revision + '^{commit}').decode().strip()
    paths = ['plugin.json', '.claude-plugin', '.codex-plugin', '.cursor-plugin',
             '.agents/plugins', 'skills', 'LICENSE', 'README.md', 'supported-skills.txt']
    archive = git('archive', '--format=tar', source, '--', *paths)
    with tarfile.open(fileobj=io.BytesIO(archive)) as package:
        files = {}
        versions = set()
        skills = []
        for member in package.getmembers():
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError('release resources must be regular files: ' + member.name)
            content = package.extractfile(member).read()
            files[member.name] = hashlib.sha256(content).hexdigest()
            if member.name.endswith('/SKILL.md') and len(Path(member.name).parts) == 3:
                skills.append(Path(member.name).parts[1])
            if member.name in {'plugin.json', '.claude-plugin/plugin.json',
                               '.codex-plugin/plugin.json', '.cursor-plugin/plugin.json'}:
                manifest = json.loads(content)
                if manifest['name'] != 'singleton-skills':
                    raise ValueError('plugin identity mismatch')
                versions.add(manifest['version'])
            marketplace_sources = {
                '.claude-plugin/marketplace.json': './',
                '.cursor-plugin/marketplace.json': '.',
                '.agents/plugins/marketplace.json': {'source': 'url', 'url': './'},
            }
            if member.name in marketplace_sources:
                marketplace = json.loads(content)
                plugins = marketplace['plugins']
                if (marketplace['name'] != 'singleton-skills' or len(plugins) != 1
                        or plugins[0]['name'] != 'singleton-skills'
                        or plugins[0]['source'] != marketplace_sources[member.name]):
                    raise ValueError('marketplace registration mismatch: ' + member.name)
                if member.name == '.claude-plugin/marketplace.json':
                    versions.add(plugins[0]['version'])
        required = {'plugin.json', '.claude-plugin/plugin.json', '.codex-plugin/plugin.json',
                    '.cursor-plugin/plugin.json', '.claude-plugin/marketplace.json',
                    '.cursor-plugin/marketplace.json', '.agents/plugins/marketplace.json'}
        if not required.issubset(files):
            raise ValueError('release registration manifests are missing')
        if len(versions) != 1 or not skills:
            raise ValueError('release versions disagree or skill inventory is empty')
    # Work treats catalogs as marketplace uploads. Keep the registration archive
    # intact and derive a standalone plugin from exactly the same committed files.
    catalogs = {'.claude-plugin/marketplace.json', '.cursor-plugin/marketplace.json',
                '.agents/plugins/marketplace.json'}
    standalone = io.BytesIO()
    with tarfile.open(fileobj=io.BytesIO(archive)) as package:
        with tarfile.open(fileobj=standalone, mode='w') as upload:
            for member in package.getmembers():
                if member.name not in catalogs:
                    upload.addfile(member, package.extractfile(member) if member.isfile() else None)
    compressed = io.BytesIO()
    with gzip.GzipFile(fileobj=compressed, mode='wb', filename='', mtime=0) as stream:
        stream.write(standalone.getvalue())
    work_archive = compressed.getvalue()
    report = {'schema_version': 1, 'plugin': 'singleton-skills',
              'version': versions.pop(), 'source_revision': source,
              'skills': sorted(skills), 'files': files,
              'archive_sha256': hashlib.sha256(archive).hexdigest(),
              'work_upload': {
                  'archive': 'singleton-skills-work.tar.gz',
                  'archive_sha256': hashlib.sha256(work_archive).hexdigest(),
                  'files': {name: digest for name, digest in files.items() if name not in catalogs},
                  'host_verification': 'pending; archive generation is not upload acceptance',
              },
              'host_verification': 'pending; preparation is not installation or publication'}
    output.mkdir(parents=True, exist_ok=False)
    (output / 'singleton-skills.tar').write_bytes(archive)
    (output / 'singleton-skills-work.tar.gz').write_bytes(work_archive)
    (output / 'release.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--revision', default='HEAD')
    args = parser.parse_args()
    try:
        prepare(args.output, args.revision)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, str(error) + '\n')
