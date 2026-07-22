/**
 * 유틸리티 함수 모음
 */

const utils = {
    showAlert(message, type = 'info', title = '알림') {
        const modal = document.getElementById('alert-modal');
        const iconEl = document.getElementById('alert-modal-icon');
        const titleEl = document.getElementById('alert-modal-title');
        const messageEl = document.getElementById('alert-modal-message');
        const closeBtn = document.getElementById('alert-modal-close-btn');

        if (!modal) {
            alert(message);
            return;
        }

        titleEl.innerText = title;
        messageEl.innerText = message;
        
        // 아이콘 설정
        iconEl.className = 'modal-icon ' + type;
        if (type === 'error') iconEl.innerText = '⚠️';
        else if (type === 'success') iconEl.innerText = '✅';
        else iconEl.innerText = 'ℹ️';

        modal.classList.add('show');

        return new Promise((resolve) => {
            closeBtn.onclick = () => {
                modal.classList.remove('show');
                resolve();
            };
            // 모달 바깥 클릭 시 닫기
            modal.onclick = (e) => {
                if (e.target === modal) {
                    modal.classList.remove('show');
                    resolve();
                }
            };
        });
    },

    formatPhoneNumber(value) {
        if (!value) return value;
        const phoneNumber = value.replace(/[^\d]/g, '');
        const phoneNumberLength = phoneNumber.length;
        if (phoneNumberLength < 4) return phoneNumber;
        if (phoneNumberLength < 8) {
            return `${phoneNumber.slice(0, 3)}-${phoneNumber.slice(3)}`;
        }
        return `${phoneNumber.slice(0, 3)}-${phoneNumber.slice(3, 7)}-${phoneNumber.slice(7, 11)}`;
    },

    handlePhoneInput(e) {
        const formattedValue = this.formatPhoneNumber(e.target.value);
        e.target.value = formattedValue;
    },

    initPasswordToggles(container = document) {
    const toggleButtons = container.querySelectorAll(
        '.password-toggle'
    );

    toggleButtons.forEach((button) => {
        button.addEventListener('click', () => {
            const targetId = button.dataset.passwordTarget;
            const input = document.getElementById(targetId);

            if (!input) return;

            // 표시 상태를 변경해도 선택 영역과 커서 위치를 유지
            const selectionStart = input.selectionStart;
            const selectionEnd = input.selectionEnd;
            const selectionDirection = input.selectionDirection;

            const willShow = input.type === 'password';

            input.type = willShow ? 'text' : 'password';

            const currentLabel =
                button.getAttribute('aria-label') || '비밀번호 보기';

            const fieldName = currentLabel.replace(
                /\s+(보기|숨기기)$/,
                ''
            );

            button.textContent = willShow ? '숨기기' : '보기';
            button.setAttribute(
                'aria-label',
                `${fieldName} ${willShow ? '숨기기' : '보기'}`
            );
            button.setAttribute(
                'aria-pressed',
                String(willShow)
            );

            if (
                selectionStart !== null &&
                selectionEnd !== null
            ) {
                input.setSelectionRange(
                    selectionStart,
                    selectionEnd,
                    selectionDirection || 'none'
                );
            }
        });
    });
},

    templatesCache: {},

    resetPasswordToggles(container = document) {
    const toggleButtons = container.querySelectorAll(
        '.password-toggle'
    );

    toggleButtons.forEach((button) => {
        const targetId = button.dataset.passwordTarget;
        const input = document.getElementById(targetId);

        if (!input) return;

        const currentLabel =
            button.getAttribute('aria-label') || '비밀번호 보기';

        const fieldName = currentLabel.replace(
            /\s+(보기|숨기기)$/,
            ''
        );

        input.type = 'password';
        button.textContent = '보기';
        button.setAttribute('aria-pressed', 'false');
        button.setAttribute(
            'aria-label',
            `${fieldName} 보기`
        );
    });
},

    async loadTemplate(name) {
        if (this.templatesCache[name]) return this.templatesCache[name];
        const response = await fetch(
            `/static/templates/${name}.html?v=20260722-2`
        );
        const html = await response.text();
        this.templatesCache[name] = html;
        return html;
    }
};
