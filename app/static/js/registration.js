/**
 * 10-Step Interactive Registration & Booking Wizard with Live Validation & Anti-Duplicate Security
 */

let wizardState = {
  currentStep: 1,
  data: {
    email: '',
    password: '',
    full_name: '',
    national_id_number: '',
    birth_date: '',
    phone_number: '',
    governorate: 'الدقهلية',
    diocese: 'إبراشية بلقاس وجمصة والدير',
    church: 'دير القديسة دميانة',
    guardian_type: 'أب',
    guardian_name: '',
    guardian_phone: '',
    confession_father_name: '',
    confession_father_phone: '',
    confession_church: '',
    companion_name: '',
    companion_phone: '',
    selected_period_id: '',
    has_interval_exception: false,
    interval_exception_reason: '',
    agreed_to_rules: false
  },
  periods: [],
  idCardFile: null,
  confessionLetterFile: null,
  validationCache: {}
};

async function renderRegistrationWizard(container, initialPeriodId = null) {
  // Load draft from localStorage
  const savedDraft = localStorage.getItem('demiana_booking_draft');
  if (savedDraft) {
    try {
      const parsed = JSON.parse(savedDraft);
      wizardState.data = { ...wizardState.data, ...parsed };
    } catch(e) {}
  }
  if (initialPeriodId) {
    wizardState.data.selected_period_id = initialPeriodId;
  }

  // Fetch available periods
  try {
    wizardState.periods = await apiCall('/periods');
  } catch (err) {
    wizardState.periods = [];
  }

  container.innerHTML = `
    <div class="container" style="max-width:820px; padding-top:40px; padding-bottom:80px;">
      <!-- Wizard Progress Indicators (1 to 10) -->
      <div class="wizard-progress">
        ${[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(s => `
          <div class="wizard-step-bullet ${s === 1 ? 'active' : ''}" id="step-bullet-${s}">${s}</div>
        `).join('')}
      </div>

      <div class="glass-card gold-glow" style="position:relative;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; border-bottom:1px solid var(--border-subtle); padding-bottom:12px;">
          <div>
            <h2 id="wizard-step-title" style="color:var(--primary-gold); font-size:1.35rem;">الخطوة 1: الحساب والبريد الإلكتروني</h2>
            <p id="wizard-step-desc" class="text-muted" style="font-size:0.85rem;">إنشاء حساب آمن وموثق لمتابعة حالة الحجوزات</p>
          </div>
          <span class="badge badge-under_review" id="wizard-step-badge">1 من 10</span>
        </div>

        <form id="wizard-form" onsubmit="handleWizardNext(event)">
          <div id="wizard-step-content">
            <!-- Dynamic Step Content Rendered Here -->
          </div>

          <div style="display:flex; justify-content:space-between; margin-top:30px; border-top:1px solid var(--border-subtle); padding-top:18px;">
            <button type="button" class="btn btn-secondary" id="wizard-prev-btn" style="display:none;" onclick="wizardPrevStep()">
              ← السابق
            </button>
            <div style="display:flex; gap:10px; margin-right:auto;">
              <button type="button" class="btn btn-outline-gold btn-sm" onclick="saveWizardDraft()">
                💾 حفظ كمسودة
              </button>
              <button type="submit" class="btn btn-primary" id="wizard-next-btn">
                التالي →
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  `;

  renderStep(wizardState.currentStep);
}

function saveWizardDraft() {
  saveCurrentStepData();
  localStorage.setItem('demiana_booking_draft', JSON.stringify(wizardState.data));
  showToast('تم حفظ البيانات كمسودة بنجاح', 'info');
}

function saveCurrentStepData() {
  const d = wizardState.data;
  const s = wizardState.currentStep;

  if (s === 1) {
    const emailEl = document.getElementById('w-email');
    const passEl = document.getElementById('w-pass');
    if (emailEl) d.email = emailEl.value.trim().toLowerCase();
    if (passEl) d.password = passEl.value;
  } else if (s === 2) {
    const nameEl = document.getElementById('w-name');
    const nidEl = document.getElementById('w-nid');
    const birthEl = document.getElementById('w-birth');
    if (nameEl) d.full_name = nameEl.value.trim();
    if (nidEl) d.national_id_number = nidEl.value.trim();
    if (birthEl) d.birth_date = birthEl.value;
  } else if (s === 3) {
    const phoneEl = document.getElementById('w-phone');
    if (phoneEl) d.phone_number = phoneEl.value.trim();
  } else if (s === 4) {
    const govEl = document.getElementById('w-gov');
    const dioEl = document.getElementById('w-dio');
    const chuEl = document.getElementById('w-chu');
    if (govEl) d.governorate = govEl.value.trim();
    if (dioEl) d.diocese = dioEl.value.trim();
    if (chuEl) d.church = chuEl.value.trim();
  } else if (s === 5) {
    const compName = document.getElementById('w-comp-name');
    const compPhone = document.getElementById('w-comp-phone');
    if (compName) d.companion_name = compName.value.trim();
    if (compPhone) d.companion_phone = compPhone.value.trim();
  } else if (s === 6) {
    const gType = document.getElementById('w-g-type');
    const gName = document.getElementById('w-g-name');
    const gPhone = document.getElementById('w-g-phone');
    if (gType) d.guardian_type = gType.value;
    if (gName) d.guardian_name = gName.value.trim();
    if (gPhone) d.guardian_phone = gPhone.value.trim();
  } else if (s === 7) {
    const cfName = document.getElementById('w-cf-name');
    const cfPhone = document.getElementById('w-cf-phone');
    const cfChurch = document.getElementById('w-cf-church');
    if (cfName) d.confession_father_name = cfName.value.trim();
    if (cfPhone) d.confession_father_phone = cfPhone.value.trim();
    if (cfChurch) d.confession_church = cfChurch.value.trim();
  } else if (s === 8) {
    const periodRadio = document.querySelector('input[name="w-period"]:checked');
    if (periodRadio) d.selected_period_id = periodRadio.value;
    const excChk = document.getElementById('w-exc-check');
    const excReason = document.getElementById('w-exc-reason');
    if (excChk) d.has_interval_exception = excChk.checked;
    if (excReason) d.interval_exception_reason = excReason.value.trim();
  } else if (s === 9) {
    const idFile = document.getElementById('w-id-card-input');
    const cfFile = document.getElementById('w-cf-letter-input');
    if (idFile && idFile.files[0]) wizardState.idCardFile = idFile.files[0];
    if (cfFile && cfFile.files[0]) wizardState.confessionLetterFile = cfFile.files[0];
  } else if (s === 10) {
    const rulesChk = document.getElementById('w-rules-agree');
    if (rulesChk) d.agreed_to_rules = rulesChk.checked;
  }
}

// Egyptian National ID client-side parser & validator
function parseEgyptianNationalId(nid) {
  nid = (nid || '').trim();
  if (!/^\d{14}$/.test(nid)) {
    return { valid: false, message: 'الرقم القومي يجب أن يتكون من 14 رقماً.' };
  }
  const century = nid[0];
  if (century !== '2' && century !== '3') {
    return { valid: false, message: 'خانة القرن في الرقم القومي غير صحيحة.' };
  }
  const year = (century === '2' ? '19' : '20') + nid.substring(1, 3);
  const month = nid.substring(3, 5);
  const day = nid.substring(5, 7);

  const mInt = parseInt(month, 10);
  const dInt = parseInt(day, 10);
  if (mInt < 1 || mInt > 12 || dInt < 1 || dInt > 31) {
    return { valid: false, message: 'تاريخ الميلاد بالرقم القومي غير صالح.' };
  }

  const birthDateStr = `${year}-${month}-${day}`;
  return {
    valid: true,
    birthDate: birthDateStr,
    isFemale: parseInt(nid[12], 10) % 2 === 0
  };
}

async function validateCurrentStep() {
  const d = wizardState.data;
  const s = wizardState.currentStep;
  const egyptPhoneRegex = /^01[0125][0-9]{8}$/;

  if (s === 1) {
    if (!d.email || !/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(d.email)) {
      showToast('يرجى إدخال بريد إلكتروني صحيح (مثال: name@gmail.com)', 'warning');
      return false;
    }
    if (!d.password || d.password.length < 8) {
      showToast('كلمة المرور يجب أن لا تقل عن 8 خانات وتحتوي على أحرف وأرقام', 'warning');
      return false;
    }
    const confirmEl = document.getElementById('w-pass-confirm');
    if (confirmEl && confirmEl.value !== d.password) {
      showToast('كلمتا المرور غير متطابقتين، يرجى التأكد من تطابق كلمة المرور وتأكيدها', 'warning');
      return false;
    }

    // Live pre-check duplicate & deliverability
    try {
      const check = await apiCall('/auth/check-duplicate', {
        method: 'POST',
        body: { field: 'email', email: d.email }
      });
      if (!check.is_available) {
        showToast(check.message, 'danger');
        return false;
      }
    } catch (e) {
      showToast(e.message || 'خطأ في فحص البريد الإلكتروني', 'danger');
      return false;
    }

  } else if (s === 2) {
    const parts = d.full_name ? d.full_name.trim().split(/\s+/) : [];
    if (parts.length < 3) {
      showToast('يرجى إدخال الاسم ثلاثياً على الأقل باللغة العربية', 'warning');
      return false;
    }

    if (!d.national_id_number || d.national_id_number.length !== 14) {
      showToast('الرقم القومي إلزامي ويجب أن يتكون من 14 رقماً بدقة', 'warning');
      return false;
    }

    const nidParsed = parseEgyptianNationalId(d.national_id_number);
    if (!nidParsed.valid) {
      showToast(nidParsed.message, 'danger');
      return false;
    }

    if (!d.birth_date) {
      d.birth_date = nidParsed.birthDate;
      const bEl = document.getElementById('w-birth');
      if (bEl) bEl.value = d.birth_date;
    }

    if (d.birth_date !== nidParsed.birthDate) {
      showToast(`تاريخ الميلاد (${d.birth_date}) غير متطابق مع تاريخ الميلاد بالرقم القومي (${nidParsed.birthDate})`, 'danger');
      return false;
    }

    const bDate = new Date(d.birth_date);
    const age = Math.floor((new Date() - bDate) / (365.25 * 24 * 60 * 60 * 1000));
    if (age < 14) {
      showToast('السن الأدنى للخلوة هو بداية المرحلة الثانوية (14-15 سنة)', 'danger');
      return false;
    }

    // Live pre-check duplicate National ID
    try {
      const check = await apiCall('/auth/check-duplicate', {
        method: 'POST',
        body: {
          field: 'national_id',
          national_id_number: d.national_id_number,
          birth_date: d.birth_date
        }
      });
      if (!check.is_available) {
        showToast(check.message, 'danger');
        return false;
      }

      // Check Identity similarity
      const idCheck = await apiCall('/auth/check-duplicate', {
        method: 'POST',
        body: {
          field: 'identity',
          full_name: d.full_name,
          birth_date: d.birth_date
        }
      });
      if (!idCheck.is_available) {
        showToast(idCheck.message, 'danger');
        return false;
      }
    } catch (e) {
      showToast(e.message || 'خطأ في فحص الرقم القومي', 'danger');
      return false;
    }

  } else if (s === 3) {
    const cleanPhone = d.phone_number ? d.phone_number.replace(/\s+/g, '').replace('+2', '') : '';
    if (!egyptPhoneRegex.test(cleanPhone)) {
      showToast('رقم الهاتف غير صحيح. يجب أن يكون رقماً مصرياً مكوناً من 11 رقماً يبدأ بـ (010, 011, 012, 015)', 'warning');
      return false;
    }

    // Live pre-check duplicate phone
    try {
      const check = await apiCall('/auth/check-duplicate', {
        method: 'POST',
        body: { field: 'phone', phone_number: cleanPhone }
      });
      if (!check.is_available) {
        showToast(check.message, 'danger');
        return false;
      }
    } catch (e) {
      showToast(e.message || 'خطأ في فحص رقم الهاتف', 'danger');
      return false;
    }

  } else if (s === 4) {
    if (!d.governorate || !d.diocese || !d.church) {
      showToast('يرجى إكمال المحافظة والإبراشية واسم كنيسة المتقدمة', 'warning');
      return false;
    }
  } else if (s === 6) {
    if (!d.guardian_name || d.guardian_name.trim().length < 3) {
      showToast('يرجى إدخال اسم ولي الأمر / المسؤول كاملاً', 'warning');
      return false;
    }
    const cleanGPhone = d.guardian_phone ? d.guardian_phone.replace(/\s+/g, '').replace('+2', '') : '';
    if (!egyptPhoneRegex.test(cleanGPhone)) {
      showToast('رقم هاتف ولي الأمر يجب أن يكون رقماً مصرياً صحيحاً (11 رقماً)', 'warning');
      return false;
    }
  } else if (s === 7) {
    if (!d.confession_father_name || d.confession_father_name.trim().length < 3) {
      showToast('يرجى إدخال اسم أب الاعتراف كاملاً', 'warning');
      return false;
    }
    const cleanCFPhone = d.confession_father_phone ? d.confession_father_phone.replace(/\s+/g, '').replace('+2', '') : '';
    if (!egyptPhoneRegex.test(cleanCFPhone)) {
      showToast('رقم هاتف أب الاعتراف يجب أن يكون رقماً مصرياً صحيحاً (11 رقماً)', 'warning');
      return false;
    }
  } else if (s === 8) {
    if (!d.selected_period_id) {
      showToast('يرجى اختيار فترة الخلوة المراد الحجز بها', 'warning');
      return false;
    }
  } else if (s === 10) {
    if (!d.agreed_to_rules) {
      showToast('يجب الموافقة والتعهد بالالتزام بلائحة وقوانين بيت الخلوة لإتمام الحجز', 'warning');
      return false;
    }
  }
  return true;
}

function handleNidInput(inputEl) {
  const val = inputEl.value.replace(/\D/g, '').slice(0, 14);
  inputEl.value = val;
  const statusEl = document.getElementById('nid-status-feedback');
  if (!statusEl) return;

  if (val.length === 14) {
    const res = parseEgyptianNationalId(val);
    if (res.valid) {
      statusEl.innerHTML = `<span style="color:#10B981; font-size:0.82rem;">✓ رقم قومي مصري صالح (تاريخ الميلاد: ${res.birthDate})</span>`;
      const birthEl = document.getElementById('w-birth');
      if (birthEl) {
        birthEl.value = res.birthDate;
        wizardState.data.birth_date = res.birthDate;
      }
    } else {
      statusEl.innerHTML = `<span style="color:#F43F5E; font-size:0.82rem;">✕ ${res.message}</span>`;
    }
  } else {
    statusEl.innerHTML = `<span class="text-muted" style="font-size:0.75rem;">أدخلي 14 رقماً (متبقي ${14 - val.length} أرقام)</span>`;
  }
}

function handleEmailTypoCheck(inputEl) {
  const email = (inputEl.value || '').trim().toLowerCase();
  const feedbackEl = document.getElementById('email-feedback-box');
  if (!feedbackEl) return;

  const typoMap = {
    'gmai.com': 'gmail.com', 'gmial.com': 'gmail.com', 'gmil.com': 'gmail.com', 'gamil.com': 'gmail.com', 'gmaill.com': 'gmail.com',
    'yaho.com': 'yahoo.com', 'yahooo.com': 'yahoo.com', 'hotmial.com': 'hotmail.com', 'outlok.com': 'outlook.com'
  };

  const domain = email.split('@')[1];
  if (domain && typoMap[domain]) {
    const suggested = email.split('@')[0] + '@' + typoMap[domain];
    feedbackEl.innerHTML = `
      <div style="background:rgba(245,158,11,0.15); border:1px solid #F59E0B; border-radius:6px; padding:8px 12px; margin-top:6px; font-size:0.82rem; color:#F59E0B; display:flex; justify-content:space-between; align-items:center;">
        <span>💡 هل تقصدين: <strong>${suggested}</strong>؟</span>
        <button type="button" class="btn btn-sm btn-outline-gold" style="padding:2px 8px; font-size:0.75rem;" onclick="applyEmailSuggestion('${suggested}')">
          تصحيح تلقائي
        </button>
      </div>
    `;
  } else {
    feedbackEl.innerHTML = '';
  }
}

function applyEmailSuggestion(suggested) {
  const emailEl = document.getElementById('w-email');
  if (emailEl) {
    emailEl.value = suggested;
    wizardState.data.email = suggested;
    const feedbackEl = document.getElementById('email-feedback-box');
    if (feedbackEl) feedbackEl.innerHTML = '<span style="color:#10B981; font-size:0.8rem;">✓ تم تصحيح البريد الإلكتروني بنجاح</span>';
  }
}

function renderStep(step) {
  const content = document.getElementById('wizard-step-content');
  const title = document.getElementById('wizard-step-title');
  const desc = document.getElementById('wizard-step-desc');
  const badge = document.getElementById('wizard-step-badge');
  const prevBtn = document.getElementById('wizard-prev-btn');
  const nextBtn = document.getElementById('wizard-next-btn');

  // Update Bullets
  for (let i = 1; i <= 10; i++) {
    const b = document.getElementById(`step-bullet-${i}`);
    if (b) {
      b.className = `wizard-step-bullet ${i === step ? 'active' : i < step ? 'completed' : ''}`;
    }
  }

  badge.innerText = `${step} من 10`;
  prevBtn.style.display = step > 1 ? 'block' : 'none';
  nextBtn.innerText = step === 10 ? '✓ تأكيد وإرسال طلب الحجز' : 'التالي →';
  if (step === 10) {
    nextBtn.className = 'btn btn-primary btn-gold';
  } else {
    nextBtn.className = 'btn btn-primary';
  }

  const d = wizardState.data;

  if (step === 1) {
    title.innerText = 'الخطوة 1: الحساب والبريد الإلكتروني';
    desc.innerText = 'سيتم إرسال رمز تأكيد فوري (OTP) إلى بريدكِ لتفعيل الحساب ومتابعة الحجز';
    content.innerHTML = `
      <div class="form-group">
        <label class="form-label required">البريد الإلكتروني المعتمد (Gmail / Outlook / Yahoo)</label>
        <input type="email" id="w-email" class="form-control" placeholder="example@gmail.com" value="${d.email}" required dir="ltr" 
               oninput="handleEmailTypoCheck(this)" />
        <div id="email-feedback-box"></div>
        <span class="text-muted" style="font-size:0.75rem;">يجب أن يكون بريداً حقيقياً مفعلاً حيث ستصل إليه رسالة تأكيد الحساب ورمز التحقق (OTP).</span>
      </div>

      <div class="form-group">
        <label class="form-label required">كلمة المرور</label>
        <div class="password-input-wrapper">
          <input type="password" id="w-pass" class="form-control" placeholder="••••••••" value="${d.password}" required minlength="8" 
                 oninput="updatePasswordStrength(this.value, 'w-strength-bar', 'w-strength-text')" />
          <button type="button" class="btn-toggle-password" onclick="togglePasswordVisibility('w-pass', this)" title="إظهار/إخفاء كلمة المرور">
            👁️
          </button>
        </div>
        <div class="password-strength-container">
          <div class="password-strength-bar"><div id="w-strength-bar" class="password-strength-fill"></div></div>
          <div id="w-strength-text" class="password-strength-text"><span>قوة كلمة المرور</span> <span>-</span></div>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label required">تأكيد كلمة المرور</label>
        <div class="password-input-wrapper">
          <input type="password" id="w-pass-confirm" class="form-control" placeholder="••••••••" value="${d.password}" required minlength="8" />
          <button type="button" class="btn-toggle-password" onclick="togglePasswordVisibility('w-pass-confirm', this)" title="إظهار/إخفاء كلمة المرور">
            👁️
          </button>
        </div>
      </div>
    `;
  } else if (step === 2) {
    title.innerText = 'الخطوة 2: البيانات الشخصية والرقم القومي';
    desc.innerText = 'الاسم الرسمي والرقم القومي كما هو مدون ببطاقة الرقم القومي المصرية';
    content.innerHTML = `
      <div class="form-group">
        <label class="form-label required">الاسم بالكامل (ثلاثي أو رباعي بالعربية) *</label>
        <input type="text" id="w-name" class="form-control" placeholder="مثال: ماري جرجس بطرس حنا" value="${d.full_name}" required />
      </div>

      <div class="form-group">
        <label class="form-label required">الرقم القومي المصري (14 رقماً) *</label>
        <input type="text" id="w-nid" maxlength="14" class="form-control" placeholder="29901151201234" value="${d.national_id_number || ''}" required dir="ltr"
               oninput="handleNidInput(this)" />
        <div id="nid-status-feedback" style="margin-top:4px;"></div>
        <span class="text-muted" style="font-size:0.75rem;">الرقم القومي هو المعرف الرسمي الفريد، ولا يمكن تسجيل أكثر من حساب بنفس الرقم القومي.</span>
      </div>

      <div class="form-group">
        <label class="form-label required">تاريخ الميلاد *</label>
        <input type="date" id="w-birth" class="form-control" value="${d.birth_date}" required />
        <span class="text-muted" style="font-size:0.75rem;">السن الأدنى المسموح به هو بداية المرحلة الثانوية (14-15 سنة). يتم استخراجه ومطابقته تلقائياً مع الرقم القومي.</span>
      </div>
    `;
  } else if (step === 3) {
    title.innerText = 'الخطوة 3: رقم الهاتف والتواصل';
    desc.innerText = 'رقم هاتف المتقدمة للتواصل وإرسال إشعارات الواتساب الرسمية وتأكيد الحجز';
    content.innerHTML = `
      <div class="form-group">
        <label class="form-label required">رقم هاتف المتقدمة (موبايل مصري به واتساب) *</label>
        <input type="tel" id="w-phone" class="form-control" placeholder="01012345678" value="${d.phone_number}" required dir="ltr" />
        <span class="text-muted" style="font-size:0.75rem;">11 رقماً يبدأ بـ 010 أو 011 أو 012 أو 015. لا يمكن مشاركة نفس الهاتف في أكثر من حساب مستقل.</span>
      </div>
    `;
  } else if (step === 4) {
    title.innerText = 'الخطوة 4: المحافظة والإبراشية والكنيسة';
    desc.innerText = 'بيانات التبعية الكنسية والجغرافية للمتقدمة';
    content.innerHTML = `
      <div class="form-group">
        <label>المحافظة *</label>
        <select id="w-gov" class="form-control" required>
          ${['الدقهلية', 'القاهرة', 'الجيزة', 'الإسكندرية', 'الغربية', 'الشرقية', 'المنوفية', 'دمياط', 'كفر الشيخ', 'القليوبية', 'البحيرة', 'بني سويف', 'المنيا', 'أسيوط', 'سوهاج', 'قنا', 'الأقصر', 'أسوان', 'البحر الأحمر', 'الوادي الجديد', 'مطروح', 'شمال سيناء', 'جنوب سيناء', 'بورسعيد', 'الإسماعيلية', 'السويس', 'الفيوم'].map(g => `
            <option value="${g}" ${d.governorate === g ? 'selected' : ''}>${g}</option>
          `).join('')}
        </select>
      </div>
      <div class="form-group">
        <label>الإبراشية التابعة لها *</label>
        <input type="text" id="w-dio" class="form-control" placeholder="مثال: إبراشية المنصورة وتوابعها" value="${d.diocese}" required />
      </div>
      <div class="form-group">
        <label>كنيسة المتقدمة *</label>
        <input type="text" id="w-chu" class="form-control" placeholder="مثال: كنيسة الشهيد مارجرجس" value="${d.church}" required />
      </div>
    `;
  } else if (step === 5) {
    title.innerText = 'الخطوة 5: بيانات المرافقة (للقاصرات فقط)';
    desc.innerText = 'القاصرات (أقل من 18 عاماً) يشترط قدومهن بصحبة تاسوني أو أخت كبرى مسؤولة';
    content.innerHTML = `
      <div class="alert-spiritual" style="margin-bottom:15px;">
        ℹ️ إذا كان سن المتقدمة أقل من 18 سنة عند موعد الخلوة، يلزم إلزامياً تعبئة اسم ورقم هاتف المرافقة.
      </div>
      <div class="form-group">
        <label>اسم المرافقة المسؤولة (تاسوني / أخت كبرى)</label>
        <input type="text" id="w-comp-name" class="form-control" placeholder="اختياري للبالغات / إلزامي للقاصرات" value="${d.companion_name || ''}" />
      </div>
      <div class="form-group">
        <label>رقم هاتف المرافقة</label>
        <input type="tel" id="w-comp-phone" class="form-control" placeholder="010XXXXXXXX" value="${d.companion_phone || ''}" dir="ltr" />
      </div>
    `;
  } else if (step === 6) {
    title.innerText = 'الخطوة 6: بيانات ولي الأمر / المسؤول';
    desc.innerText = 'للتواصل في حالات الطوارئ والتنسيق قبل السفر';
    content.innerHTML = `
      <div class="form-group">
        <label>صلة القرابة *</label>
        <select id="w-g-type" class="form-control">
          ${['أب', 'أم', 'زوج', 'أخ', 'ولي أمر'].map(t => `
            <option value="${t}" ${d.guardian_type === t ? 'selected' : ''}>${t}</option>
          `).join('')}
        </select>
      </div>
      <div class="form-group">
        <label>اسم ولي الأمر بالكامل *</label>
        <input type="text" id="w-g-name" class="form-control" placeholder="الاسم ثلاثياً" value="${d.guardian_name}" required />
      </div>
      <div class="form-group">
        <label>رقم هاتف ولي الأمر *</label>
        <input type="tel" id="w-g-phone" class="form-control" placeholder="012XXXXXXXX" value="${d.guardian_phone}" required dir="ltr" />
      </div>
    `;
  } else if (step === 7) {
    title.innerText = 'الخطوة 7: بيانات أب الاعتراف';
    desc.innerText = 'المرجعية الروحية للمتقدمة والتزكية';
    content.innerHTML = `
      <div class="form-group">
        <label>اسم أب الاعتراف (قدس أبونا) *</label>
        <input type="text" id="w-cf-name" class="form-control" placeholder="مثال: القمص يوحنا زكريا" value="${d.confession_father_name}" required />
      </div>
      <div class="form-group">
        <label>رقم هاتف أب الاعتراف *</label>
        <input type="tel" id="w-cf-phone" class="form-control" placeholder="011XXXXXXXX" value="${d.confession_father_phone}" required dir="ltr" />
      </div>
      <div class="form-group">
        <label>كنيسة أب الاعتراف *</label>
        <input type="text" id="w-cf-church" class="form-control" placeholder="مثال: كنيسة الشهيد مارجرجس" value="${d.confession_church}" required />
      </div>
    `;
  } else if (step === 8) {
    title.innerText = 'الخطوة 8: اختيار فترة الخلوة والاستثناء';
    desc.innerText = 'تحديد الموعد المناسب لطلب الخلوة بالدير';

    const periodsHtml = (wizardState.periods || []).map(p => `
      <label class="period-select-card ${d.selected_period_id === p.id ? 'selected' : ''}" style="display:block; padding:12px; margin-bottom:10px; border-radius:8px; border:1px solid ${d.selected_period_id === p.id ? 'var(--primary-gold)' : 'var(--border-subtle)'}; cursor:pointer;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <input type="radio" name="w-period" value="${p.id}" ${d.selected_period_id === p.id ? 'checked' : ''} onchange="selectWizardPeriod('${p.id}')" />
            <strong style="color:var(--text-gold); margin-right:8px;">${p.title}</strong>
          </div>
          <span class="badge ${p.available_capacity > 0 ? 'badge-approved' : 'badge-under_review'}">
            ${p.available_capacity > 0 ? `متاح ${p.available_capacity} سرير` : 'قائمة انتظار'}
          </span>
        </div>
        <div style="font-size:0.85rem; color:var(--text-muted); margin-top:6px;">
          📅 من ${p.start_date} إلى ${p.end_date}
        </div>
      </label>
    `).join('');

    content.innerHTML = `
      <div class="form-group">
        <label class="form-label required">الفترات المتاحة للحجز:</label>
        <div style="max-height:220px; overflow-y:auto;">
          ${periodsHtml || '<p class="text-muted">لا توجد فترات متاحة حالياً.</p>'}
        </div>
      </div>

      <div class="form-group" style="margin-top:15px; background:rgba(0,0,0,0.2); padding:12px; border-radius:8px;">
        <label style="display:flex; align-items:center; gap:8px; cursor:pointer;">
          <input type="checkbox" id="w-exc-check" ${d.has_interval_exception ? 'checked' : ''} onchange="toggleExceptionReason(this)" />
          <span style="font-size:0.9rem;">طلب استثناء من الفاصل الزمني (3 أشهر بين الخلوات)</span>
        </label>
        <div id="w-exc-reason-box" style="display:${d.has_interval_exception ? 'block' : 'none'}; margin-top:10px;">
          <textarea id="w-exc-reason" class="form-control" rows="2" placeholder="اكتبي سبب طلب الاستثناء لعرضه على الأم المسؤولة...">${d.interval_exception_reason || ''}</textarea>
        </div>
      </div>
    `;
  } else if (step === 9) {
    title.innerText = 'الخطوة 9: إرفاق المستندات والتزكية';
    desc.innerText = 'رفع صورة بطاقة الرقم القومي وتزكية أب الاعتراف (اختياري الآن ويمكن رفعه لاحقاً)';
    content.innerHTML = `
      <div class="form-group">
        <label>صورة بطاقة الرقم القومي (الوجه الأمامي)</label>
        <input type="file" id="w-id-card-input" class="form-control" accept="image/*,.pdf" />
        <span class="text-muted" style="font-size:0.75rem;">الملفات المسموح بها: JPG, PNG, PDF (بحد أقصى 5 ميجابايت).</span>
      </div>
      <div class="form-group">
        <label>صورة خطاب تزكية / موافقة أب الاعتراف</label>
        <input type="file" id="w-cf-letter-input" class="form-control" accept="image/*,.pdf" />
        <span class="text-muted" style="font-size:0.75rem;">تأكيد خطي أو خطاب رسمي مختوم من كنيسة أب الاعتراف.</span>
      </div>
    `;
  } else if (step === 10) {
    title.innerText = 'الخطوة 10: مراجعة التعهد واللائحة الروحية';
    desc.innerText = 'الموافقة على شروط وقوانين الإقامة والالتزام ببيت الخلوة بالدير';
    content.innerHTML = `
      <div class="glass-card" style="max-height:220px; overflow-y:auto; font-size:0.85rem; line-height:1.8; margin-bottom:20px; background:rgba(0,0,0,0.3); padding:15px; border:1px solid rgba(212,175,55,0.3);">
        <h4 style="color:var(--primary-gold); margin-top:0;">تعهد وضوابط بيت الخلوة بدير القديسة دميانة:</h4>
        <ol style="padding-right:20px;">
          <li>الالتزام التام بالهدوء والصمت والروحانية داخل أروقة الدير والقلالي.</li>
          <li>الحضور في المواعيد المحددة لصلوات القداس الإلهي، المجمع، وتسبحة نصف الليل.</li>
          <li>إطفاء الأنوار والتزام الصمت التام داخل القلاية وغلقها بالمفتاح من الساعة 11:00 مساءً حتى 6:00 صباحاً.</li>
          <li>ممنوع منعاً باتاً التصوير داخل القلالي أو ممر بيت الخلوة الداخلي.</li>
          <li>ممنوع التواجد خارج بيت الخلوة بعد الساعة 4:30 مساءً.</li>
          <li>عدم مغادرة الدير أو استقبال زوار إلا بإذن مسبق من الأم المسؤولة.</li>
        </ol>
      </div>

      <div class="form-group">
        <label style="display:flex; align-items:center; gap:10px; cursor:pointer;">
          <input type="checkbox" id="w-rules-agree" ${d.agreed_to_rules ? 'checked' : ''} required />
          <strong style="color:var(--text-light); font-size:0.95rem;">أتعهد أنا المتقدمة بالالتزام الكامل بكافة قوانين ولائحة بيت الخلوة بدير القديسة دميانة.</strong>
        </label>
      </div>

      <div style="text-align:center; padding:15px; background:rgba(212,175,55,0.06); border-radius:10px; border:1px dashed var(--primary-gold);">
        <div style="font-size:2.5rem; margin-bottom:8px;">☩</div>
        <h4 style="color:var(--primary-gold); margin-bottom:6px;">أنتِ على وشك إرسال طلب الخلوة</h4>
        <p class="text-muted" style="font-size:0.85rem; margin:0;">
          سيتم إرسال رمز تأكيد فوري (OTP) للبريد الإلكتروني لتأكيد التسجيل ورفع الطلب للأم المسؤولة.
        </p>
      </div>
    `;
  }
}

function selectWizardPeriod(periodId) {
  wizardState.data.selected_period_id = periodId;
  const cards = document.querySelectorAll('.period-select-card');
  cards.forEach(c => c.style.borderColor = 'var(--border-subtle)');
  const radio = document.querySelector(`input[name="w-period"][value="${periodId}"]`);
  if (radio && radio.closest('.period-select-card')) {
    radio.closest('.period-select-card').style.borderColor = 'var(--primary-gold)';
  }
}

function toggleExceptionReason(chk) {
  const box = document.getElementById('w-exc-reason-box');
  if (box) box.style.display = chk.checked ? 'block' : 'none';
}

function wizardPrevStep() {
  if (wizardState.currentStep > 1) {
    saveCurrentStepData();
    wizardState.currentStep--;
    renderStep(wizardState.currentStep);
  }
}

async function handleWizardNext(event) {
  event.preventDefault();
  saveCurrentStepData();

  const isValid = await validateCurrentStep();
  if (!isValid) {
    return;
  }

  if (wizardState.currentStep < 10) {
    wizardState.currentStep++;
    renderStep(wizardState.currentStep);
  } else {
    // Final Submission
    await submitWizardRegistration();
  }
}

async function submitWizardRegistration() {
  const d = wizardState.data;
  showToast('جاري تسجيل الحساب والتحقق من صحة البيانات...', 'info');

  try {
    // 1. Register User & Profile with National ID
    const regRes = await apiCall('/auth/register', {
      method: 'POST',
      body: {
        email: d.email,
        password: d.password,
        full_name: d.full_name,
        national_id_number: d.national_id_number,
        birth_date: d.birth_date,
        phone_number: d.phone_number,
        governorate: d.governorate,
        diocese: d.diocese,
        church: d.church,
        guardian_type: d.guardian_type,
        guardian_name: d.guardian_name,
        guardian_phone: d.guardian_phone,
        confession_father_name: d.confession_father_name,
        confession_father_phone: d.confession_father_phone,
        confession_church: d.confession_church,
        companion_name: d.companion_name,
        companion_phone: d.companion_phone
      }
    });

    // Store pending booking details in localStorage
    localStorage.setItem('demiana_pending_booking', JSON.stringify({
      period_id: d.selected_period_id,
      agreed_to_rules: d.agreed_to_rules,
      has_interval_exception: d.has_interval_exception,
      interval_exception_reason: d.interval_exception_reason
    }));

    if (regRes.requires_verification) {
      // Prompt Email OTP Modal
      showToast(regRes.message, 'success');
      openEmailVerificationModal(regRes.email);
      return;
    }

    // Direct Login (if verification disabled)
    setAuth(regRes.access_token, {
      id: regRes.user_id,
      email: regRes.email,
      role: regRes.role
    });

    await finalizePendingBooking();

  } catch (err) {
    showToast(err.message || 'حدث خطأ أثناء تقديم الطلب', 'danger');
  }
}

async function finalizePendingBooking() {
  const pending = localStorage.getItem('demiana_pending_booking');
  if (!pending) {
    navigate('guest_dashboard');
    return;
  }

  const bookingData = JSON.parse(pending);
  try {
    // 1. Upload ID card document if selected
    if (wizardState.idCardFile) {
      const formData = new FormData();
      formData.append('doc_type', 'NATIONAL_ID_FRONT');
      formData.append('file', wizardState.idCardFile);
      await apiCall('/profile/upload-document', {
        method: 'POST',
        body: formData,
        isFormData: true
      }).catch(e => console.warn('ID Upload warning:', e));
    }

    // 2. Upload Confession letter if selected
    if (wizardState.confessionLetterFile) {
      const formData2 = new FormData();
      formData2.append('doc_type', 'CONFESSION_LETTER');
      formData2.append('file', wizardState.confessionLetterFile);
      await apiCall('/profile/upload-document', {
        method: 'POST',
        body: formData2,
        isFormData: true
      }).catch(e => console.warn('Letter Upload warning:', e));
    }

    // 3. Submit Booking
    const bookingRes = await apiCall('/bookings/submit', {
      method: 'POST',
      body: bookingData
    });

    localStorage.removeItem('demiana_booking_draft');
    localStorage.removeItem('demiana_pending_booking');

    showToast(`تم تقديم طلب الخلوة بنجاح! رقم الحجز: ${bookingRes.booking_reference}`, 'success');
    navigate('guest_dashboard');
  } catch (err) {
    showToast(err.message || 'حدث خطأ أثناء تأكيد الحجز', 'danger');
    navigate('guest_dashboard');
  }
}
