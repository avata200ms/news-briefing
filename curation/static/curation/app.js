/**
 * AI 뉴스 큐레이터 인터랙션 스크립트
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM 엘리먼트 참조
    const inputKeyword = document.getElementById('input-keyword');
    const inputFilterPrompt = document.getElementById('input-filter-prompt');
    const toggleDemoMode = document.getElementById('toggle-demo-mode');
    const btnCurate = document.getElementById('btn-curate');
    const presetChipsContainer = document.getElementById('preset-chips-container');

    const loadingPanel = document.getElementById('loading-panel');
    const loadingTitle = document.getElementById('loading-title');
    const loadingSubtitle = document.getElementById('loading-subtitle');
    const stepNaver = document.getElementById('step-naver');
    const stepGemini = document.getElementById('step-gemini');

    const resultsSection = document.getElementById('results-section');
    const resKeyword = document.getElementById('res-keyword');
    const resMetaInfo = document.getElementById('res-meta-info');
    const demoBanner = document.getElementById('demo-banner');
    const curatedCardsContainer = document.getElementById('curated-cards-container');
    const rawArticlesContainer = document.getElementById('raw-articles-container');
    const btnToggleRaw = document.getElementById('btn-toggle-raw');
    const btnScrollToSearch = document.getElementById('btn-scroll-to-search');
    const btnSaveAllResults = document.getElementById('btn-save-all-results');

    // 현재 큐레이션 결과 캐싱 (저장 시 활용)
    let lastCurationResult = null;

    // 모달 엘리먼트
    const apiModalBackdrop = document.getElementById('api-modal-backdrop');
    const btnOpenApiModal = document.getElementById('btn-open-api-modal');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const btnModalConfirm = document.getElementById('btn-modal-confirm');

    // CSRF 토큰 추출
    function getCsrfToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        if (cookieValue) return cookieValue;

        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfInput ? csrfInput.value : '';
    }

    // =========================================================================
    // 1. 프리셋 칩 클릭 이벤트
    // =========================================================================
    presetChipsContainer.addEventListener('click', (e) => {
        const btn = e.target.closest('.chip-btn');
        if (!btn) return;

        const keyword = btn.dataset.keyword;
        const filter = btn.dataset.filter;

        if (keyword && filter) {
            inputKeyword.value = keyword;
            inputFilterPrompt.value = filter;
            inputKeyword.focus();

            // 부드러운 강조 효과
            inputKeyword.style.transition = 'all 0.3s ease';
            inputFilterPrompt.style.transition = 'all 0.3s ease';
            inputKeyword.style.borderColor = '#818cf8';
            inputFilterPrompt.style.borderColor = '#818cf8';

            setTimeout(() => {
                inputKeyword.style.borderColor = '';
                inputFilterPrompt.style.borderColor = '';
            }, 600);
        }
    });

    // =========================================================================
    // 2. 큐레이션 실행 핸들러
    // =========================================================================
    btnCurate.addEventListener('click', async () => {
        const keyword = inputKeyword.value.trim();
        const filterPrompt = inputFilterPrompt.value.trim();
        const allowDemo = toggleDemoMode.checked;

        if (!keyword) {
            alert('검색 키워드를 입력해 주세요.');
            inputKeyword.focus();
            return;
        }

        if (!filterPrompt) {
            alert('기사를 선별할 AI 필터링 프롬프트를 입력해 주세요.');
            inputFilterPrompt.focus();
            return;
        }

        // UI 상태: 로딩 시작
        setLoadingState(true);

        try {
            // 단계 1 시각 효과
            updateLoadingStep(1);

            // 단계 2 전환 타이머 (사용자 경험 개선)
            const stepTimer = setTimeout(() => {
                updateLoadingStep(2);
            }, 1200);

            const response = await fetch('/api/curate/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify({
                    keyword: keyword,
                    filter_prompt: filterPrompt,
                    allow_demo: allowDemo,
                }),
            });

            clearTimeout(stepTimer);
            const data = await response.json();

            if (data.status === 'success') {
                renderResults(data.data);
            } else {
                handleApiError(data);
            }
        } catch (err) {
            console.error('Request failed:', err);
            alert('네트워크 통신 중 오류가 발생했습니다. 서버 연결 상태를 확인해 주세요.');
        } finally {
            setLoadingState(false);
        }
    });

    // 로딩 상태 제어
    function setLoadingState(isLoading) {
        if (isLoading) {
            btnCurate.disabled = true;
            btnCurate.querySelector('.btn-text').textContent = 'AI 분석 진행 중...';
            loadingPanel.style.display = 'block';
            resultsSection.style.display = 'none';

            loadingPanel.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
            btnCurate.disabled = false;
            btnCurate.querySelector('.btn-text').textContent = 'AI 큐레이션 실행';
            loadingPanel.style.display = 'none';
        }
    }

    function updateLoadingStep(step) {
        if (step === 1) {
            stepNaver.classList.add('active');
            stepGemini.classList.remove('active');
            loadingTitle.textContent = '네이버 뉴스 20건을 수집하고 있습니다...';
            loadingSubtitle.textContent = '최신 기사 데이터를 안전하게 정제하는 중입니다.';
        } else if (step === 2) {
            stepNaver.classList.remove('active');
            stepGemini.classList.add('active');
            loadingTitle.textContent = 'Gemini 2.5 AI가 기사를 심층 분석 중입니다...';
            loadingSubtitle.textContent = '필터링 기준에 가장 부합하는 3개 기사를 엄선하고 3줄 요약 및 인사이트를 도출합니다.';
        }
    }

    // =========================================================================
    // 3. 결과 렌더링
    // =========================================================================
    function renderResults(result) {
        lastCurationResult = result;
        resKeyword.textContent = result.keyword;
        resMetaInfo.textContent = `네이버 검색 20건 중 선정 완료 • 필터: "${result.filter_prompt}"`;

        // 전체 저장 버튼 상태 초기화
        if (btnSaveAllResults) {
            btnSaveAllResults.disabled = false;
            btnSaveAllResults.querySelector('span').textContent = '3건 전체 저장하기';
        }

        // 데모 모드 배너 (상세 에러 원인 안내)
        if (result.metadata && result.metadata.is_demo) {
            demoBanner.style.display = 'flex';
            const errorMsg = result.metadata.original_error;
            const bannerSpan = demoBanner.querySelector('span');
            if (bannerSpan) {
                if (errorMsg) {
                    if (errorMsg.includes('401') || errorMsg.includes('Authentication failed')) {
                        bannerSpan.innerHTML = `<strong>[네이버 검색 API 인증 실패 (401)]</strong> 네이버 개발자 센터에서 Client ID/Secret 및 'API 설정 &gt; 검색' 권한이 켜져 있는지 확인해 주세요. (현재 데모 데이터 시연 중)`;
                    } else if (errorMsg.includes('Gemini')) {
                        bannerSpan.innerHTML = `<strong>[Gemini AI 호출 오류]</strong> ${escapeHtml(errorMsg)} (현재 데모 데이터 시연 중)`;
                    } else {
                        bannerSpan.innerHTML = `<strong>[외부 API 오류]</strong> ${escapeHtml(errorMsg)} (현재 데모 데이터 시연 중)`;
                    }
                } else {
                    bannerSpan.innerHTML = `현재 .env의 API 키가 비어있어 <strong>시뮬레이션 데모 데이터</strong>로 시연되었습니다. 실제 실시간 뉴스를 조회하려면 .env에 네이버 및 Gemini API 키를 입력해주세요.`;
                }
            }
        } else {
            demoBanner.style.display = 'none';
        }

        // 3대 엄선 기사 렌더링
        curatedCardsContainer.innerHTML = '';
        const rankLabels = ['1위 선정 기사', '2위 선정 기사', '3위 선정 기사'];

        result.curated_articles.forEach((art, index) => {
            const rank = index + 1;
            const rankLabel = rankLabels[index] || `${rank}위 기사`;

            const card = document.createElement('article');
            card.className = `news-card rank-${rank}`;

            // 3줄 요약 리스트 HTML
            const summaryBulletsHtml = (art.summary_bullets || [])
                .map(item => `
                    <li class="summary-item">
                        <span class="summary-bullet"></span>
                        <span>${escapeHtml(item)}</span>
                    </li>
                `).join('');

            card.innerHTML = `
                <div class="card-top-bar">
                    <span class="rank-badge rank-${rank}">
                        ★ ${rankLabel}
                    </span>
                    <span class="article-origin-index">수집 원본 ${art.article_index}번 기사</span>
                </div>

                <h3 class="card-title">${escapeHtml(art.title)}</h3>

                <div class="reason-box">
                    <strong>🎯 AI 선정 이유:</strong>
                    <span>${escapeHtml(art.reason)}</span>
                </div>

                <div class="summary-section">
                    <h4 class="section-subtitle">핵심 요약 (3 Bullets)</h4>
                    <ul class="summary-list">
                        ${summaryBulletsHtml}
                    </ul>
                </div>

                <div class="insight-callout">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"></path>
                    </svg>
                    <div>
                        <strong>핵심 인사이트:</strong> ${escapeHtml(art.key_insight)}
                    </div>
                </div>

                <div class="card-bottom-bar">
                    <button type="button" class="btn-save-article" data-index="${index}">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                            <polyline points="17 21 17 13 7 13 7 21"></polyline>
                            <polyline points="7 3 7 8 15 8"></polyline>
                        </svg>
                        <span>결과 저장하기</span>
                    </button>
                    <a href="${art.link}" target="_blank" rel="noopener noreferrer" class="btn-read-origin">
                        기사 원문 보러가기
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="7" y1="17" x2="17" y2="7"></line>
                            <polyline points="7 7 17 7 17 17"></polyline>
                        </svg>
                    </a>
                </div>
            `;
            curatedCardsContainer.appendChild(card);
        });

        // 카드별 저장 버튼 이벤트 리스너 바인딩
        document.querySelectorAll('.btn-save-article').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const idx = parseInt(btn.dataset.index, 10);
                const art = result.curated_articles[idx];
                if (!art) return;

                btn.disabled = true;
                btn.querySelector('span').textContent = '저장 중...';

                try {
                    const saveRes = await fetch('/api/save/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrfToken(),
                        },
                        body: JSON.stringify({
                            title: art.title,
                            summary_bullets: art.summary_bullets,
                            link: art.link,
                            reason: art.reason,
                            key_insight: art.key_insight,
                            keyword: result.keyword,
                        }),
                    });
                    const saveData = await saveRes.json();

                    if (saveData.status === 'success') {
                        btn.classList.add('saved');
                        btn.querySelector('span').textContent = '저장 완료 ✓';
                    } else {
                        alert(saveData.message || '저장에 실패했습니다.');
                        btn.disabled = false;
                        btn.querySelector('span').textContent = '결과 저장하기';
                    }
                } catch (err) {
                    console.error('Save failed:', err);
                    alert('네트워크 오류로 저장을 완료하지 못했습니다.');
                    btn.disabled = false;
                    btn.querySelector('span').textContent = '결과 저장하기';
                }
            });
        });

        // 20개 전체 원본 기사 렌더링
        rawArticlesContainer.innerHTML = '';
        (result.raw_articles || []).forEach(item => {
            const rawEl = document.createElement('div');
            rawEl.className = 'raw-item';
            rawEl.innerHTML = `
                <div class="raw-index">#${item.index}</div>
                <div class="raw-info">
                    <a href="${item.link}" target="_blank" rel="noopener noreferrer" class="raw-item-title">
                        ${escapeHtml(item.title)}
                    </a>
                    <div class="raw-item-desc">${escapeHtml(item.description)}</div>
                </div>
            `;
            rawArticlesContainer.appendChild(rawEl);
        });

        // 결과 표시 및 스크롤
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // 에러 핸들러
    function handleApiError(data) {
        if (data.code === 'MISSING_API_KEY') {
            if (confirm(`${data.message}\n\n지금 바로 API Key 설정 안내 창을 여시겠습니까?`)) {
                openApiModal();
            }
        } else {
            alert(`오류: ${data.message || '요청 처리에 실패했습니다.'}`);
        }
    }

    // =========================================================================
    // 4. 전체 저장, 아코디언 & 검색 복귀 버튼
    // =========================================================================
    if (btnSaveAllResults) {
        btnSaveAllResults.addEventListener('click', async () => {
            if (!lastCurationResult || !lastCurationResult.curated_articles) {
                alert('저장할 큐레이션 결과가 없습니다.');
                return;
            }

            btnSaveAllResults.disabled = true;
            btnSaveAllResults.querySelector('span').textContent = '저장 중...';

            try {
                const response = await fetch('/api/save/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken(),
                    },
                    body: JSON.stringify({
                        items: lastCurationResult.curated_articles,
                        keyword: lastCurationResult.keyword,
                    }),
                });
                const data = await response.json();

                if (data.status === 'success') {
                    btnSaveAllResults.querySelector('span').textContent = '전체 3건 저장 완료 ✓';
                    document.querySelectorAll('.btn-save-article').forEach(btn => {
                        btn.classList.add('saved');
                        btn.querySelector('span').textContent = '저장 완료 ✓';
                        btn.disabled = true;
                    });
                    if (confirm('3건의 기사가 히스토리에 저장되었습니다!\n지금 "나의 요약 히스토리"로 이동하시겠습니까?')) {
                        window.location.href = '/history/';
                    }
                } else {
                    alert(data.message || '저장에 실패했습니다.');
                    btnSaveAllResults.disabled = false;
                    btnSaveAllResults.querySelector('span').textContent = '3건 전체 저장하기';
                }
            } catch (err) {
                console.error('Save all failed:', err);
                alert('통신 오류로 저장을 완료하지 못했습니다.');
                btnSaveAllResults.disabled = false;
                btnSaveAllResults.querySelector('span').textContent = '3건 전체 저장하기';
            }
        });
    }

    btnToggleRaw.addEventListener('click', () => {
        const isExpanded = btnToggleRaw.classList.contains('expanded');
        if (isExpanded) {
            btnToggleRaw.classList.remove('expanded');
            rawArticlesContainer.style.display = 'none';
        } else {
            btnToggleRaw.classList.add('expanded');
            rawArticlesContainer.style.display = 'flex';
        }
    });

    btnScrollToSearch.addEventListener('click', () => {
        inputKeyword.focus();
        inputKeyword.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });

    // =========================================================================
    // 5. 모달 제어
    // =========================================================================
    function openApiModal() {
        apiModalBackdrop.style.display = 'flex';
    }

    function closeApiModal() {
        apiModalBackdrop.style.display = 'none';
    }

    btnOpenApiModal.addEventListener('click', openApiModal);
    btnCloseModal.addEventListener('click', closeApiModal);
    btnModalConfirm.addEventListener('click', closeApiModal);

    apiModalBackdrop.addEventListener('click', (e) => {
        if (e.target === apiModalBackdrop) {
            closeApiModal();
        }
    });

    // HTML escape 유틸리티
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
