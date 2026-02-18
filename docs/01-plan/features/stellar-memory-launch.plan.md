# Plan: stellar-memory-launch

## 개요

Stellar Memory v1.0.0 코드 완성 및 GitHub 저장소/랜딩 페이지 배포 이후,
**실제 사용자가 설치하고 사용할 수 있는 상태**로 만들기 위한 출시 종합 계획.

## 현재 상태 (AS-IS)

| 항목 | 상태 | 문제점 |
|------|:----:|--------|
| GitHub 저장소 | ✅ | https://github.com/sangjun0000/stellar-memory |
| 랜딩 페이지 | ✅ | https://sangjun0000.github.io/stellar-memory/ |
| 코드 v1.0.0 | ✅ | 603 tests, 60 modules |
| pyproject.toml | ⚠️ | version="0.9.0", URL이 잘못된 org 가리킴 |
| LICENSE 파일 | ❌ | 없음 (MIT 선언만 있음) |
| CHANGELOG | ⚠️ | v1.0.0 (P9) 항목 없음 |
| README 배지 URLs | ⚠️ | `stellar-memory/stellar-memory` → `sangjun0000/stellar-memory` |
| PyPI 배포 | ❌ | `pip install stellar-memory` 불가 |
| Docker Hub | ❌ | 이미지 미배포 |
| GitHub Release | ❌ | v1.0.0 태그 없음 |
| MkDocs 문서 사이트 | ❌ | 빌드/배포 안됨 |
| GitHub Discussions | ❌ | 비활성화 |

## 목표 (TO-BE)

```
사용자가 할 수 있는 것:
1. pip install stellar-memory       ← PyPI에서 설치
2. docker pull sangjun0000/stellar-memory  ← Docker Hub에서 실행
3. GitHub README 보고 Quick Start 따라하기
4. 랜딩 페이지에서 프로젝트 이해
5. MkDocs 문서 사이트에서 API 레퍼런스 확인
6. GitHub Releases에서 v1.0.0 다운로드
7. GitHub Discussions에서 질문
```

---

## 기능 목록 (Features)

### F1: 프로젝트 메타데이터 정비
**우선순위**: P0 (최우선 - 다른 모든 것의 전제 조건)

- [ ] `pyproject.toml` version → `1.0.0`
- [ ] `pyproject.toml` URLs → `sangjun0000/stellar-memory`로 수정
- [ ] `pyproject.toml` Development Status → `5 - Production/Stable`
- [ ] `pyproject.toml` Homepage → GitHub Pages 랜딩 페이지
- [ ] LICENSE 파일 생성 (MIT)
- [ ] CHANGELOG.md에 v1.0.0 (P9) 항목 추가
- [ ] README.md 배지 URL 수정 (`sangjun0000/stellar-memory`)
- [ ] README.md에 GitHub Pages 링크 추가
- [ ] `__init__.py` fallback version → `1.0.0`

**성공 기준**: 모든 파일의 버전/URL이 일관성 있게 v1.0.0, sangjun0000 가리킴

### F2: PyPI 배포
**우선순위**: P0 (핵심 배포)

- [ ] `python -m build`로 sdist + wheel 생성
- [ ] `twine check dist/*`로 패키지 검증
- [ ] TestPyPI에 먼저 시험 배포 (`twine upload --repository testpypi`)
- [ ] TestPyPI에서 설치 테스트 (`pip install -i https://test.pypi.org/simple/ stellar-memory`)
- [ ] PyPI에 정식 배포 (`twine upload dist/*`)
- [ ] `pip install stellar-memory` 설치 확인

**전제 조건**: F1 완료, PyPI 계정 필요
**성공 기준**: `pip install stellar-memory && python -c "import stellar_memory; print(stellar_memory.__version__)"` → `1.0.0`

### F3: GitHub Release & Tag
**우선순위**: P0

- [ ] `git tag v1.0.0` 생성
- [ ] `gh release create v1.0.0` 릴리스 노트 작성
- [ ] 릴리스에 wheel/sdist 첨부

**성공 기준**: https://github.com/sangjun0000/stellar-memory/releases/tag/v1.0.0 접속 가능

### F4: MkDocs 문서 사이트 배포
**우선순위**: P1 (중요하지만 F1-F3 이후)

- [ ] `mkdocs.yml` site_url 수정
- [ ] `mkdocs build`로 빌드 확인
- [ ] GitHub Pages에 문서 사이트 배포 (gh-pages 브랜치 /docs/ 경로)
  - 또는: 별도 서브도메인으로 배포
- [ ] 랜딩 페이지 "Docs" 링크 연결

**성공 기준**: 문서 사이트 온라인 접근 가능

### F5: Docker Hub 배포
**우선순위**: P1

- [ ] Docker Hub 계정/저장소 생성
- [ ] `docker build -t sangjun0000/stellar-memory:1.0.0 .`
- [ ] `docker push sangjun0000/stellar-memory:1.0.0`
- [ ] `docker push sangjun0000/stellar-memory:latest`
- [ ] Docker Hub README 작성

**전제 조건**: Docker Hub 계정, Docker Desktop 실행
**성공 기준**: `docker pull sangjun0000/stellar-memory` 성공

### F6: CI/CD 파이프라인 수정
**우선순위**: P1

- [ ] `.github/workflows/ci.yml` - 저장소 경로 수정
- [ ] `.github/workflows/release.yml` - PyPI 토큰 시크릿 설정
- [ ] GitHub Actions secrets 등록 (PYPI_API_TOKEN)
- [ ] CI 워크플로우 실행 확인 (push 후 테스트 통과)

**성공 기준**: GitHub Actions 그린 체크 ✅

### F7: 커뮤니티 & 발견성 (Discoverability)
**우선순위**: P2 (출시 후)

- [ ] GitHub Discussions 활성화
- [ ] GitHub Topics 설정 (ai, memory, llm, mcp, python)
- [ ] GitHub Description 확인
- [ ] GitHub Social Preview 이미지 (og:image)
- [ ] 랜딩 페이지 OG 메타태그 추가 (이미 있으면 확인)

**성공 기준**: GitHub 저장소 검색 가능, 공유 시 프리뷰 표시

---

## 구현 순서

```
F1 (메타데이터 정비) ──→ F2 (PyPI) ──→ F3 (Release)
                    ╲                         │
                     ──→ F6 (CI/CD) ──────────┤
                                              ↓
                         F4 (MkDocs) ──→ F7 (커뮤니티)
                         F5 (Docker) ──↗
```

**Phase 1** (즉시): F1 → F2 → F3 (메타데이터 → PyPI → Release)
**Phase 2** (이후): F4, F5, F6 (문서, Docker, CI/CD)
**Phase 3** (출시 후): F7 (커뮤니티)

---

## 리스크 & 제약사항

| 리스크 | 영향 | 대응 |
|--------|------|------|
| PyPI에 `stellar-memory` 이름이 이미 점유 | 높음 | 사전 확인 필요, 대안: `stellar-mem` |
| Docker Desktop 미설치 | 중간 | F5 건너뛰기 가능 |
| PyPI 계정 없음 | 높음 | 계정 생성 + API 토큰 발급 필요 |
| MkDocs 빌드 의존성 | 낮음 | `pip install mkdocs-material` |

---

## 예상 결과물

완료 시 사용자 경험:
```bash
# 1. 설치 (3초)
pip install stellar-memory

# 2. 바로 사용
python -c "
from stellar_memory import StellarMemory
m = StellarMemory()
m.store('Python은 간결한 문법을 가진 언어이다')
results = m.recall('프로그래밍 언어')
print(results[0].content)
"

# 3. CLI
stellar-memory store "중요한 정보"
stellar-memory recall "정보 검색"

# 4. Docker
docker run -p 8000:8000 sangjun0000/stellar-memory
```

---

**작성일**: 2026-02-18
**버전 목표**: v1.0.0 정식 릴리스
**예상 Feature 수**: 7 (F1~F7)
