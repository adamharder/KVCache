from attr import define
from pathlib import Path
from werkzeug.utils import secure_filename
import arrow
import json

@define
class KVCacheMetadata:
    touch_ts: arrow.Arrow
    created_ts: arrow.Arrow
    ttl_ts: arrow.Arrow

    @staticmethod
    def build(ttl_secs:int=None):
        now_ts=arrow.now()
        ttl_ts=now_ts.shift(years=+100)
        if ttl_secs is not None:
            ttl_ts=now_ts.shift(seconds=+ttl_secs)
        return KVCacheMetadata(touch_ts=now_ts, created_ts=now_ts, ttl_ts=ttl_ts)
    @staticmethod
    def from_json(json_obj):
        return KVCacheMetadata(
            touch_ts=arrow.get(json_obj["touch_ts"]), 
            created_ts=arrow.get(json_obj["created_ts"]), 
            ttl_ts=arrow.get(json_obj["ttl_ts"])
        )
    @property
    def as_json(self):
        return dict(created_ts=str(self.created_ts),
                          touch_ts=str(self.touch_ts),
                          ttl_ts=str(self.ttl_ts))


class KVCache(object):
    def __init__(self, root_dir:Path=None):
        if root_dir is None:
            root_dir = Path(__file__).parent/"KV_CACHE"
            root_dir.mkdir(exist_ok=True)
        assert root_dir.is_dir()
        self._root_dir=root_dir
        self._data_dir=root_dir
        self.data_dir.mkdir(exist_ok=True)
        self.metadata_dir.mkdir(exist_ok=True)
    @property
    def data_dir(self):
        return self._root_dir/"data"
    @property
    def metadata_dir(self):
        return self._root_dir/"metadata"

    def get_metadata(self, key:str):
        metadata_file=self.metadata_dir/secure_filename(key)
        if metadata_file.is_file():
            return KVCacheMetadata.from_json(json.loads(metadata_file.read_text()))
        return None

    def touch_metadata(self, key:str, ttl_secs=None):
        now_ts=arrow.now()

        metadata=self.get_metadata(key)
        if metadata is None:
            metadata=KVCacheMetadata.build(ttl_secs)
        metadata.touch_ts=now_ts
        if ttl_secs is not None:
            metadata.ttl_ts=now_ts.shift(seconds=+ttl_secs)
        metadata_file=self.metadata_dir/secure_filename(key)
        metadata_file.write_text(json.dumps(metadata.as_json))
        
    def keys(self, pattern):
        r=[]
        for item in self.data_dir.glob(pattern):
            r.append(item.name)
        return r

    def get(self, key:str)->bytes:
        internal_key=secure_filename(key)
        metadata_file=self.metadata_dir/internal_key
        data_file = self.data_dir/internal_key
        if metadata_file.is_file():
            metadata=self.get_metadata(key)
            if metadata.ttl_ts < arrow.now():
                # the file is expired
                data_file.unlink()
                metadata_file.unlink()
        if data_file.is_file():
            self.touch_metadata(key)
            return data_file.read_bytes()
        return None

    def get_ttl(self, key):
        md=self.get_metadata(key)
        if md is None:
            return -1
        return md[""]-arrow.now().total_seconds


    def set_val(self, key:str, val:bytes):
        assert isinstance(key, str)
        assert secure_filename(key) == key, f"key {key} contains illegal characters."
        if isinstance(val, list):
            val=json.dumps(val)
        if isinstance(val, dict):
            val=json.dumps(val)
        if isinstance(val, int):
            val=str(val)
        if isinstance(val, str):
            val=val.encode()
        assert isinstance(val, bytes)
        data_file = self.data_dir/secure_filename(key)
        data_file.write_bytes(val)
        self.touch_metadata(key)

    def expire(self, key, ttl_secs=None):
        self.touch_metadata(key, ttl_secs)
        if ttl_secs is not None:
            if ttl_secs<1:
                self.get(key)

