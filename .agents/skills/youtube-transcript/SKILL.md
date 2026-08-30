---
name: youtube-transcript
description: YouTube 동영상 URL에서 자막(스크립트)을 매우 빠르고 안정적으로 추출합니다.
---

# YouTube Transcript

이 스킬은 `yt-dlp`를 사용하여 오디오 처리(STT) 없이 YouTube 자막(스크립트)을 직접 추출합니다.
추출 속도가 매우 빠르고 다양한 차단 기술을 우회할 수 있어 안정적입니다.

## 사용 방법

에이전트는 유튜브 영상을 분석해야 할 때 아래 파이썬 스크립트를 호출하여 자막 텍스트를 얻을 수 있습니다.

```bash
python3 catalog/skills/youtube-transcript/scripts/extract.py <YouTube URL>
```
(참고: 스킬이 `.agents/skills`에 설치된 경우 경로를 맞춰서 사용하세요.)

출력은 정제된 평문 자막 텍스트이며, 이를 바탕으로 요약, 번역, 분석을 수행하면 됩니다.

## 제한사항
- 동영상에 캡션(자동 생성 자막 포함)이 전혀 없는 경우 추출할 수 없습니다.
- 시스템에 `yt-dlp`가 설치되어 있어야 합니다. (설치 안 된 경우 스크립트가 안내 문구를 출력함)
