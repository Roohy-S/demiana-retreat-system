/**
 * Saint Demiana Retreat Management System - Core Application Script
 */

const AppState = {
  token: localStorage.getItem('demiana_token') || null,
  user: JSON.parse(localStorage.getItem('demiana_user') || 'null'),
  currentView: 'landing',
  privacyMode: false,
  notifications: [],
  pendingVerificationEmail: null
};

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = String(text);
  return div.innerHTML;
}

// API Client Helper
async function apiCall(endpoint, options = {}) {
  const headers = options.headers || {};
  if (AppState.token) {
    headers['Authorization'] = `Bearer ${AppState.token}`;
  }
  if (!options.isFormData && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const fetchOptions = {
    method: options.method || 'GET',
    headers: headers,
  };

  if (options.body) {
    fetchOptions.body = options.isFormData ? options.body : JSON.stringify(options.body);
  }

  const urlPrefixes = ['/api/v1', '/api', '/v1', ''];
  let lastError = null;

  for (const prefix of urlPrefixes) {
    try {
      const url = `${prefix}${endpoint}`;
      const response = await fetch(url, fetchOptions);

      if (response.status === 405 || response.status === 404) {
        continue;
      }

      // Check if error response
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        const msg = errData.detail || 'حدث خطأ في معالجة الطلب';

        // Check if email verification is required
        if (response.status === 403 && msg.includes('EMAIL_NOT_VERIFIED')) {
          const ident = options.body ? (options.body.email || options.body.identifier || '') : '';
          openEmailVerificationModal(ident);
          throw new Error('يرجى تأكيد حسابكِ برمز التحقق (OTP) المرسل إلى بريدك الإلكتروني');
        }

        if (response.status === 401 && AppState.token) {
          logout();
          showToast('انتهت الجلسة، يرجى تسجيل الدخول مجدداً', 'warning');
        }

        throw new Error(msg);
      }

      // If PDF or blob
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/pdf')) {
        return await response.blob();
      }

      return await response.json();
    } catch (err) {
      lastError = err;
      if (err.message && !err.message.includes('405') && !err.message.includes('Not Found') && !err.message.includes('Failed to fetch')) {
        throw err;
      }
    }
  }

  if (lastError) throw lastError;
  throw new Error('حدث خطأ في معالجة الطلب');
}

// Toast Notifications
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type} glass-card`;
  toast.style.cssText = `
    min-width: 280px;
    padding: 14px 18px;
    margin-bottom: 10px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    gap: 10px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.5);
    animation: slideInRight 0.3s ease;
    border-right: 4px solid ${type === 'success' ? '#10B981' : type === 'warning' ? '#F59E0B' : type === 'danger' ? '#F43F5E' : '#38BDF8'};
  `;
  
  const icon = type === 'success' ? '✓' : type === 'warning' ? '⚠' : type === 'danger' ? '✕' : 'ℹ';
  toast.innerHTML = `<span style="font-weight:bold; font-size:1.2rem;">${icon}</span> <span>${message}</span>`;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Global Auth Functions
function setAuth(token, user) {
  AppState.token = token;
  AppState.user = user;
  localStorage.setItem('demiana_token', token);
  localStorage.setItem('demiana_user', JSON.stringify(user));
  updateNavUI();
}

function logout() {
  AppState.token = null;
  AppState.user = null;
  localStorage.removeItem('demiana_token');
  localStorage.removeItem('demiana_user');
  updateNavUI();
  navigate('landing');
  showToast('تم تسجيل الخروج بنجاح', 'info');
}

// View Routing
function navigate(viewName, params = {}) {
  AppState.currentView = viewName;
  const mainContent = document.getElementById('main-content');
  if (!mainContent) return;

  window.scrollTo({ top: 0, behavior: 'smooth' });

  if (viewName === 'landing') {
    renderLandingView(mainContent);
  } else if (viewName === 'guest_dashboard') {
    renderGuestDashboard(mainContent);
  } else if (viewName === 'admin_dashboard') {
    renderAdminDashboard(mainContent);
  } else if (viewName === 'register_wizard') {
    renderRegistrationWizard(mainContent, params.selectedPeriodId);
  } else if (viewName === 'login') {
    renderLoginView(mainContent);
  }
}

// Modal Helpers
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('show');
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('show');
  }
}

// Header Navigation UI Update
function updateNavUI() {
  const navActions = document.getElementById('nav-actions');
  if (!navActions) return;

  if (AppState.token && AppState.user) {
    const isStaff = AppState.user.role !== 'APPLICANT';
    navActions.innerHTML = `
      <span class="user-greeting" style="font-size:0.9rem; color:var(--text-gold); font-weight:600;">
        ${isStaff ? 'لوحة الإدارة' : 'حسابي'} (${AppState.user.email.split('@')[0]})
      </span>
      <button class="btn btn-sm btn-outline-gold" onclick="navigate('${isStaff ? 'admin_dashboard' : 'guest_dashboard'}')">
        ${isStaff ? 'لوحة التحكم الإدارية' : 'لوحة الحجوزات'}
      </button>
      <button class="btn btn-sm btn-danger" onclick="logout()">خروج</button>
    `;
  } else {
    navActions.innerHTML = `
      <button class="btn btn-sm btn-secondary" onclick="navigate('login')">تسجيل الدخول</button>
      <button class="btn btn-sm btn-primary" onclick="navigate('register_wizard')">طلب خلوة جديد</button>
    `;
  }
}

// ==============================================================================
// Arabic Date Formatters & Helpers (Day - Month - Year / يوم - شهر - سنة)
// ==============================================================================
const ARABIC_DAY_NAMES = ['الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'];
const ARABIC_MONTH_NAMES = [
  'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
  'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
];

function formatArabicDate(dateStr) {
  if (!dateStr) return '-';
  try {
    const parts = dateStr.split('T')[0].split('-');
    if (parts.length !== 3) return dateStr;
    const y = parseInt(parts[0], 10);
    const m = parseInt(parts[1], 10);
    const d = parseInt(parts[2], 10);
    const dateObj = new Date(y, m - 1, d);
    const dayName = ARABIC_DAY_NAMES[dateObj.getDay()] || '';
    const monthName = ARABIC_MONTH_NAMES[m - 1] || '';
    const padD = String(d).padStart(2, '0');
    const padM = String(m).padStart(2, '0');
    return `${dayName} ${padD}-${padM}-${y} (${padD} ${monthName} ${y})`;
  } catch (e) {
    return dateStr;
  }
}

function formatShortDate(dateStr) {
  if (!dateStr) return '-';
  try {
    const parts = dateStr.split('T')[0].split('-');
    if (parts.length !== 3) return dateStr;
    const y = parseInt(parts[0], 10);
    const m = parseInt(parts[1], 10);
    const d = parseInt(parts[2], 10);
    const dateObj = new Date(y, m - 1, d);
    const dayName = ARABIC_DAY_NAMES[dateObj.getDay()] || '';
    const padD = String(d).padStart(2, '0');
    const padM = String(m).padStart(2, '0');
    return `${dayName} ${padD}-${padM}-${y}`;
  } catch (e) {
    return dateStr;
  }
}

function calculateAge(birthDateStr) {
  if (!birthDateStr) return '-';
  try {
    const parts = birthDateStr.split('T')[0].split('-');
    if (parts.length !== 3) return '-';
    const birthYear = parseInt(parts[0], 10);
    const birthMonth = parseInt(parts[1], 10) - 1;
    const birthDay = parseInt(parts[2], 10);
    const today = new Date();
    let age = today.getFullYear() - birthYear;
    const m = today.getMonth() - birthMonth;
    if (m < 0 || (m === 0 && today.getDate() < birthDay)) {
      age--;
    }
    return age >= 0 ? age : '-';
  } catch (e) {
    return '-';
  }
}

function formatDayMonthOnly(dateStr) {
  if (!dateStr) return '-';
  try {
    const parts = dateStr.split('T')[0].split('-');
    if (parts.length !== 3) return dateStr;
    const y = parseInt(parts[0], 10);
    const m = parseInt(parts[1], 10);
    const d = parseInt(parts[2], 10);
    const dateObj = new Date(y, m - 1, d);
    const dayName = ARABIC_DAY_NAMES[dateObj.getDay()] || '';
    const monthName = ARABIC_MONTH_NAMES[m - 1] || '';
    const padD = String(d).padStart(2, '0');
    return `${dayName} ${padD} ${monthName}`;
  } catch (e) {
    return dateStr;
  }
}

function addDaysToDate(dateStr, daysCount) {
  if (!dateStr) return '';
  try {
    const parts = dateStr.split('-');
    const dateObj = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
    dateObj.setDate(dateObj.getDate() + daysCount);
    const y = dateObj.getFullYear();
    const m = String(dateObj.getMonth() + 1).padStart(2, '0');
    const d = String(dateObj.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  } catch (e) {
    return '';
  }
}

function calculateDateDifference(startDateStr, endDateStr) {
  if (!startDateStr || !endDateStr) return 0;
  try {
    const d1 = new Date(startDateStr);
    const d2 = new Date(endDateStr);
    const diffTime = d2.getTime() - d1.getTime();
    const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));
    return diffDays > 0 ? diffDays : 0;
  } catch (e) {
    return 0;
  }
}

// Privacy Mask Formatter
function maskPhone(phone) {
  if (!AppState.privacyMode || !phone) return phone;
  if (phone.length <= 4) return '****';
  return phone.slice(0, 3) + '****' + phone.slice(-3);
}

// ==============================================================================
// Password Visibility Toggle & Strength Helpers
// ==============================================================================
function togglePasswordVisibility(inputId, btnEl) {
  const input = document.getElementById(inputId);
  if (!input) return;

  if (input.type === 'password') {
    input.type = 'text';
    if (btnEl) {
      btnEl.innerHTML = '👁️‍🗨️';
      btnEl.title = 'إخفاء كلمة المرور';
      btnEl.style.color = 'var(--primary-gold)';
    }
  } else {
    input.type = 'password';
    if (btnEl) {
      btnEl.innerHTML = '👁️';
      btnEl.title = 'إظهار كلمة المرور';
      btnEl.style.color = 'var(--text-muted)';
    }
  }
}

function updatePasswordStrength(password, barFillId, textLabelId) {
  const bar = document.getElementById(barFillId);
  const text = document.getElementById(textLabelId);
  if (!bar || !text) return;

  if (!password) {
    bar.className = 'password-strength-fill';
    bar.style.width = '0%';
    text.innerHTML = '<span>قوة كلمة المرور</span> <span>-</span>';
    return;
  }

  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++;
  else if (/[A-Za-z]/.test(password)) score += 0.5;
  if (/\d/.test(password)) score++;
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score++;

  if (score < 2) {
    bar.className = 'password-strength-fill strength-weak';
    text.innerHTML = '<span>قوة كلمة المرور:</span> <span style="color:#F43F5E; font-weight:700;">ضعيفة (يجب 8 خانات وأحرف وأرقام)</span>';
  } else if (score < 3.5) {
    bar.className = 'password-strength-fill strength-medium';
    text.innerHTML = '<span>قوة كلمة المرور:</span> <span style="color:#F59E0B; font-weight:700;">متوسطة (جيدة)</span>';
  } else {
    bar.className = 'password-strength-fill strength-strong';
    text.innerHTML = '<span>قوة كلمة المرور:</span> <span style="color:#10B981; font-weight:700;">قوية وممتازة ✓</span>';
  }
}

// ==============================================================================
// Email OTP Verification Modal Logic
// ==============================================================================
let otpTimerInterval = null;

function openEmailVerificationModal(email, devOtp = null) {
  AppState.pendingVerificationEmail = email;
  let modal = document.getElementById('email-otp-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'email-otp-modal';
    modal.className = 'modal-backdrop';
    document.body.appendChild(modal);
  }

  const devOtpBanner = devOtp ? `
    <div style="background:rgba(212, 175, 55, 0.16); border:1.5px dashed var(--primary-gold); padding:12px 16px; border-radius:12px; margin-bottom:18px; text-align:center;">
      <div style="font-size:0.84rem; color:var(--text-gold); margin-bottom:4px;">🔑 رمز التحقق المباشر (للتجربة السريعة):</div>
      <div style="font-size:1.6rem; font-weight:900; color:#FFFFFF; letter-spacing:8px; font-family:monospace;">${devOtp}</div>
      <div style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">(تم وضعه تلقائياً في الخانة أدناه لسهولة التجربة)</div>
    </div>
  ` : '';

  modal.innerHTML = `
    <div class="modal-card glass-card animate-scale-in" style="max-width:500px; text-align:center;">
      <div style="font-size:2.8rem; color:var(--primary-gold); margin-bottom:12px;">📧</div>
      <h3 style="color:var(--primary-gold); margin-bottom:8px;">تأكيد وتفعيل الحساب (Email OTP)</h3>
      <p style="font-size:0.92rem; color:var(--text-secondary); line-height:1.6; margin-bottom:16px;">
        تم إرسال رمز تحقق مكون من 6 أرقام إلى بريدكِ الإلكتروني:<br>
        <strong style="color:var(--primary-gold); direction:ltr; display:inline-block; font-size:1.05rem; margin-top:4px;">${email}</strong>
      </p>

      ${devOtpBanner}

      <div class="form-group" style="margin-bottom:20px;">
        <label style="font-weight:700; margin-bottom:8px; display:block; color:var(--text-primary);">أدخلي رمز التحقق (6 أرقام):</label>
        <input type="text" id="otp-input" maxlength="6" class="form-control" 
               placeholder="123456" 
               value="${devOtp || ''}"
               style="text-align:center; font-size:2rem; letter-spacing:10px; font-weight:bold; font-family:monospace; padding:12px; border-color:var(--primary-gold);"
               autocomplete="one-time-code" autofocus />
      </div>

      <div id="otp-timer-display" style="font-size:0.85rem; color:#F59E0B; margin-bottom:22px;">
        ⏱️ الرمز صالح لمدة: <span id="otp-timer-seconds" style="font-weight:700;">15:00</span>
      </div>

      <div style="display:flex; flex-direction:column; gap:12px;">
        <button class="btn btn-primary btn-block" onclick="submitEmailOtpVerification()" style="font-size:1rem; padding:12px;">
          ✓ تأكيد وتفعيل الحساب
        </button>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
          <button id="resend-otp-btn" class="btn btn-sm btn-outline-gold" onclick="resendEmailOtp()">
            🔄 إعادة إرسال الرمز
          </button>
          <button class="btn btn-sm btn-secondary" onclick="closeModal('email-otp-modal')">
            إلغاء
          </button>
        </div>
      </div>
    </div>
  `;

  modal.classList.add('show');
  startOtpCountdown(15 * 60);

  // Auto focus input
  setTimeout(() => {
    const input = document.getElementById('otp-input');
    if (input) input.focus();
  }, 250);
}

function startOtpCountdown(durationSeconds) {
  if (otpTimerInterval) clearInterval(otpTimerInterval);
  let timeLeft = durationSeconds;

  const timerSpan = document.getElementById('otp-timer-seconds');
  if (!timerSpan) return;

  otpTimerInterval = setInterval(() => {
    timeLeft--;
    if (timeLeft <= 0) {
      clearInterval(otpTimerInterval);
      timerSpan.innerText = 'منتهي الصلاحية';
      timerSpan.style.color = 'var(--accent-rose)';
      return;
    }
    const mins = Math.floor(timeLeft / 60);
    const secs = timeLeft % 60;
    timerSpan.innerText = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }, 1000);
}

async function submitEmailOtpVerification() {
  const otpInput = document.getElementById('otp-input');
  if (!otpInput) return;
  const otp = otpInput.value.trim();

  if (otp.length !== 6 || !/^\d{6}$/.test(otp)) {
    showToast('يرجى إدخال رمز التحقق المكون من 6 أرقام بدقة', 'warning');
    return;
  }

  try {
    const res = await apiCall('/auth/verify-email', {
      method: 'POST',
      body: {
        email: AppState.pendingVerificationEmail,
        otp_code: otp
      }
    });

    closeModal('email-otp-modal');
    if (otpTimerInterval) clearInterval(otpTimerInterval);

    setAuth(res.access_token, {
      id: res.user_id,
      email: res.email,
      role: res.role
    });

    showToast('تم تأكيد البريد وتفعيل الحساب بنجاح! بركة القديسة دميانة معكِ.', 'success');

    if (typeof finalizePendingBooking === 'function' && localStorage.getItem('demiana_pending_booking')) {
      await finalizePendingBooking();
    } else {
      navigate('guest_dashboard');
    }
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

async function resendEmailOtp() {
  if (!AppState.pendingVerificationEmail) return;
  const btn = document.getElementById('resend-otp-btn');
  if (btn) btn.disabled = true;

  try {
    await apiCall('/auth/resend-verification-code', {
      method: 'POST',
      body: { email: AppState.pendingVerificationEmail }
    });
    showToast('تم إرسال رمز تحقق جديد إلى بريدكِ الإلكتروني بنجاح', 'success');
    startOtpCountdown(15 * 60);
  } catch (err) {
    showToast(err.message, 'danger');
  } finally {
    setTimeout(() => {
      if (btn) btn.disabled = false;
    }, 10000);
  }
}

// ==============================================================================
// Forgot Password & Reset Password Modals
// ==============================================================================
let resetPasswordEmail = '';

function openForgotPasswordModal() {
  let modal = document.getElementById('forgot-password-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'forgot-password-modal';
    modal.className = 'modal-backdrop';
    document.body.appendChild(modal);
  }

  modal.innerHTML = `
    <div class="modal-card glass-card animate-scale-in" style="max-width:480px;">
      <div style="text-align:center; margin-bottom:20px;">
        <div style="font-size:2.6rem; color:var(--primary-gold); margin-bottom:8px;">🔒</div>
        <h3 style="color:var(--primary-gold); margin-bottom:6px;">استعادة كلمة المرور</h3>
        <p class="text-muted" style="font-size:0.88rem;">
          أدخلي بريدكِ الإلكتروني المسجل، أو رقم الهاتف، أو الرقم القومي وسنرسل لكِ رمز تحقق (OTP)
        </p>
      </div>

      <div id="forgot-step-1">
        <form onsubmit="handleForgotRequestSubmit(event)">
          <div class="form-group">
            <label class="form-label required">البريد الإلكتروني أو رقم الهاتف أو الرقم القومي</label>
            <input type="text" id="forgot-identifier" class="form-control" placeholder="example@gmail.com أو 01012345678 أو الرقم القومي" required dir="auto" />
          </div>

          <div style="display:flex; flex-direction:column; gap:10px; margin-top:20px;">
            <button type="submit" id="forgot-submit-btn" class="btn btn-primary btn-block">
              إرسال رمز التحقق ➔
            </button>
            <button type="button" class="btn btn-secondary btn-block" onclick="closeModal('forgot-password-modal')">
              إلغاء
            </button>
          </div>
        </form>
      </div>

      <div id="forgot-step-2" style="display:none;">
        <form onsubmit="handleResetPasswordSubmit(event)">
          <p class="text-muted" style="font-size:0.85rem; margin-bottom:15px;">
            تم إرسال رمز التحقق إلى: <strong id="reset-target-email" style="color:var(--primary-gold); direction:ltr;"></strong>
          </p>

          <div class="form-group">
            <label class="form-label required">رمز التحقق (6 أرقام)</label>
            <input type="text" id="reset-otp" class="form-control" maxlength="6" placeholder="123456" 
                   style="text-align:center; font-size:1.6rem; letter-spacing:8px; font-weight:bold; font-family:monospace;" required />
          </div>

          <div class="form-group">
            <label class="form-label required">كلمة المرور الجديدة</label>
            <div class="password-input-wrapper">
              <input type="password" id="reset-new-pass" class="form-control" placeholder="••••••••" required minlength="8" 
                     oninput="updatePasswordStrength(this.value, 'reset-strength-bar', 'reset-strength-text')" />
              <button type="button" class="btn-toggle-password" onclick="togglePasswordVisibility('reset-new-pass', this)">👁️</button>
            </div>
            <div class="password-strength-container">
              <div class="password-strength-bar"><div id="reset-strength-bar" class="password-strength-fill"></div></div>
              <div id="reset-strength-text" class="password-strength-text"><span>قوة كلمة المرور</span> <span>-</span></div>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label required">تأكيد كلمة المرور الجديدة</label>
            <div class="password-input-wrapper">
              <input type="password" id="reset-confirm-pass" class="form-control" placeholder="••••••••" required minlength="8" />
              <button type="button" class="btn-toggle-password" onclick="togglePasswordVisibility('reset-confirm-pass', this)">👁️</button>
            </div>
          </div>

          <div style="display:flex; flex-direction:column; gap:10px; margin-top:22px;">
            <button type="submit" class="btn btn-primary btn-block">
              ✓ حفظ كلمة المرور الجديدة وتأكيدها
            </button>
            <button type="button" class="btn btn-secondary btn-block" onclick="closeModal('forgot-password-modal')">
              إلغاء
            </button>
          </div>
        </form>
      </div>
    </div>
  `;

  openModal('forgot-password-modal');
  setTimeout(() => {
    const el = document.getElementById('forgot-identifier');
    if (el) el.focus();
  }, 200);
}

async function handleForgotRequestSubmit(event) {
  event.preventDefault();
  const identifier = document.getElementById('forgot-identifier')?.value?.trim();
  if (!identifier) return;

  const btn = document.getElementById('forgot-submit-btn');
  if (btn) btn.disabled = true;

  try {
    const res = await apiCall('/auth/forgot-password', {
      method: 'POST',
      body: { identifier }
    });

    resetPasswordEmail = res.email || identifier;
    showToast(res.message || 'تم إرسال رمز التحقق إلى بريدكِ الإلكتروني', 'success');

    document.getElementById('forgot-step-1').style.display = 'none';
    document.getElementById('forgot-step-2').style.display = 'block';
    document.getElementById('reset-target-email').innerText = resetPasswordEmail;
    if (res.dev_otp) {
      const otpInput = document.getElementById('reset-otp');
      if (otpInput) otpInput.value = res.dev_otp;
      showToast(`💡 رمز الاستعادة المباشر: ${res.dev_otp}`, 'info');
    }
  } catch (err) {
    showToast(err.message || 'فشل إرسال رمز الاستعادة', 'danger');
  } finally {
    if (btn) btn.disabled = false;
  }
}


async function handleResetPasswordSubmit(event) {
  event.preventDefault();
  const otp = document.getElementById('reset-otp')?.value?.trim();
  const newPass = document.getElementById('reset-new-pass')?.value;
  const confirmPass = document.getElementById('reset-confirm-pass')?.value;

  if (otp.length !== 6) {
    showToast('رمز التحقق يجب أن يتكون من 6 أرقام', 'warning');
    return;
  }

  if (newPass.length < 8) {
    showToast('كلمة المرور يجب أن لا تقل عن 8 خانات وتحتوي على أحرف وأرقام', 'warning');
    return;
  }

  if (newPass !== confirmPass) {
    showToast('كلمتا المرور غير متطابقتين', 'warning');
    return;
  }

  try {
    const res = await apiCall('/auth/reset-password', {
      method: 'POST',
      body: {
        email: resetPasswordEmail,
        otp_code: otp,
        new_password: newPass
      }
    });

    closeModal('forgot-password-modal');
    showToast(res.message || 'تم تغيير كلمة المرور بنجاح!', 'success');
    navigate('login');
  } catch (err) {
    showToast(err.message || 'فشل إعادة تعيين كلمة المرور', 'danger');
  }
}

// Initial Boot
document.addEventListener('DOMContentLoaded', () => {
  updateNavUI();
  if (AppState.token && AppState.user) {
    if (AppState.user.role !== 'APPLICANT') {
      navigate('admin_dashboard');
    } else {
      navigate('guest_dashboard');
    }
  } else {
    navigate('landing');
  }
});

