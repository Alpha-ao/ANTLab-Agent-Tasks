"""Portable paths and explicit line-ending handling for historical text hashes."""
import hashlib
import pathlib

def portable_path(root,name):
    relative=pathlib.PurePosixPath(name.replace('\\','/'))
    if relative.is_absolute() or '..' in relative.parts or any(':' in p for p in relative.parts):
        raise ValueError('not a repository-relative path')
    return pathlib.Path(root).joinpath(*relative.parts)

def text_hash(raw):
    # Normalize CRLF only, never whitespace, JSON key order or code semantics.
    return hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()

def matches_hash(root,name,expected,checkout):
    raw=portable_path(root,name).read_bytes()
    if hashlib.sha256(raw).hexdigest()==expected:return True
    entry=checkout.get(name.replace('\\','/'),{})
    return entry.get('historical_raw_sha256')==expected and entry.get('lf_sha256')==text_hash(raw)
