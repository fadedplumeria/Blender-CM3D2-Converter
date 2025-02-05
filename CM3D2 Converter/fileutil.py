from __future__ import annotations

import io
import os
import shutil
import tempfile
from typing import TypeVar

from System.IO import MemoryStream
from CM3D2.Serialization import CM3D2Serializer, ICM3D2Serializable


class TemporaryFileWriter(io.BufferedWriter):
    """ファイルをアトミックに更新します。"""
    backup_filepath = None
    __filepath = None
    __temppath = None

    @property
    def filepath(self):
        """ファイルパスを取得します。"""
        return self.__filepath

    @property
    def temppath(self):
        """一時ファイルパスを取得します。"""
        return self.__temppath

    def __init__(self, filepath, mode='wb', buffer_size=io.DEFAULT_BUFFER_SIZE, backup_filepath=None):
        """ファイルパスを指定して初期化します。
        backup_filepath に None 以外が指定された場合、書き込み完了時に
        バックアップファイルが作成されます。
        """
        dirpath, filename = os.path.split(filepath)
        fd, temppath = tempfile.mkstemp(prefix=filename + '.', dir=dirpath)
        try:
            fh = os.fdopen(fd, mode)
            super(TemporaryFileWriter, self).__init__(fh, buffer_size)
        except:
            if fh:
                fh.close()
            os.remove(temppath)
            raise
        self.__filepath = filepath
        self.__temppath = temppath
        self.backup_filepath = backup_filepath

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None and exc_value is None and traceback is None:
            self.close()
        else:
            self.abort()

    def close(self):
        """一時ファイルを閉じてリネームします。"""
        if self.closed:
            return
        super(io.BufferedWriter, self).close()
        self.raw.close()
        try:
            if os.path.exists(self.filepath):
                if self.backup_filepath is not None:
                    shutil.move(self.filepath, self.backup_filepath)
                else:
                    os.remove(self.filepath)
            shutil.move(self.temppath, self.filepath)
        except:
            os.remove(self.temppath)
            raise

    def abort(self):
        """一時ファイルを閉じて削除します。"""
        if self.closed:
            return
        super(io.BufferedWriter, self).close()
        self.raw.close()
        os.remove(self.temppath)


def serialize_to_file(data: ICM3D2Serializable, file: io.BufferedWriter):
    serializer = CM3D2Serializer()
    memory_stream = MemoryStream()
    serializer.Serialize(memory_stream, data)
    file.write(bytes(memory_stream.GetBuffer())[:memory_stream.Length])

TCM3D2Serializable = TypeVar('TCM3D2Serializable', bound=ICM3D2Serializable)
def deserialize_from_file(file_type: type[TCM3D2Serializable], file: io.BufferedWriter) -> TCM3D2Serializable:
    serializer = CM3D2Serializer()
    memory_stream = MemoryStream(file.read())
    return serializer.Deserialize[file_type](memory_stream)
    