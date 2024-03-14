from typing import Tuple

import chardet


class FileUtils:
    _CHAR_DET_CONFIDENCE_THRESHOLD = 0.8

    @classmethod
    def read_text(cls, content: bytes) -> Tuple[str, str]:
        try:
            return content.decode(), 'utf-8'  # try to decode as utf-8
        except UnicodeDecodeError:  # then detect actual character encoding
            encoding = 'utf-8'  # fallback to utf-8 if no successful detection
            det_result = chardet.detect(content)
            if det_result:
                det_encoding = det_result.get('encoding')
                det_confidence = det_result.get('confidence')
                if det_encoding and det_confidence and det_confidence > cls._CHAR_DET_CONFIDENCE_THRESHOLD:
                    encoding = det_encoding
            return content.decode(encoding), encoding
