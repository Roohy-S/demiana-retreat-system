/**
 * Mother Superior & Supervisors Command Center View
 */

let adminState = {
  currentTab: 'overview',
  stats: null,
  periods: [],
  selectedCandidate: null,
  activeFilterPeriodId: '',
  activeFilterStatus: '',
  searchQuery: '',
  privacyMode: false,
  bookingsViewMode: 'cards'
};

function togglePrivacyMode() {
  adminState.privacyMode = !adminState.privacyMode;
  AppState.privacyMode = adminState.privacyMode;
  renderAdminDashboard(document.getElementById('main-content'));
}

function setBookingsViewMode(mode) {
  adminState.bookingsViewMode = mode;
  loadAdminBookings();
}

async function renderAdminDashboard(container) {
  container.innerHTML = `
    <div class="container" style="padding-top:20px; padding-bottom:80px;">
      <!-- Admin Top Banner & Controls -->
      <div class="section-header" style="flex-wrap:wrap; gap:12px;">
        <div>
          <h1 style="color:var(--primary-gold); font-size:1.6rem; display:flex; align-items:center; gap:10px;">
            <span>✝</span> لوحة تحكم الأم المسؤولة عن بيت الخلوة
          </h1>
          <p class="text-muted" style="font-size:0.85rem;">دير القديسة دميانة العامر ببراري بلقاس</p>
        </div>

        <div style="display:flex; align-items:center; gap:12px;">
          <!-- Privacy Mode Toggle -->
          <button class="btn btn-sm ${adminState.privacyMode ? 'btn-outline-gold' : 'btn-secondary'}" onclick="togglePrivacyMode()">
            <span>${adminState.privacyMode ? '🔒 وضع الخصوصية مفعّل' : '🔓 وضع الخصوصية معطل'}</span>
          </button>
          <button class="btn btn-sm btn-primary" onclick="openCreatePeriodModal()">
            <span>+</span> إنشاء فترة خلوة جديدة
          </button>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="tabs-nav" id="admin-main-tabs">
        <button class="tab-btn active" onclick="switchAdminTab('overview')">📊 نظرة عامة والأولويات</button>
        <button class="tab-btn" onclick="switchAdminTab('periods')">📅 إدارة الفترات والسعة</button>
        <button class="tab-btn" onclick="switchAdminTab('bookings')">📑 إدارة الحجوزات والطلبات</button>
        <button class="tab-btn" onclick="switchAdminTab('gate')">🚪 البوابة والاستقبال (Check-in)</button>
        <button class="tab-btn" onclick="switchAdminTab('reports')">📈 التقارير و PDF</button>
        <button class="tab-btn" onclick="switchAdminTab('duplicates')">🛡️ تدقيق ومنع التكرار</button>
        <button class="tab-btn" onclick="switchAdminTab('staff')">👥 المشرفون والصلاحيات</button>
        <button class="tab-btn" onclick="switchAdminTab('settings')">⚙️ إعدادات النظام والقواعد</button>
      </div>

      <!-- Dynamic Tab Content Area -->
      <div id="admin-tab-content">
        <!-- Injected via switchAdminTab -->
      </div>
    </div>

    <!-- Candidate Dossier Modal -->
    <div id="candidate-dossier-modal" class="modal-backdrop">
      <div class="modal-content" style="max-width:900px;">
        <div class="modal-header">
          <h3 id="dossier-candidate-name" style="color:var(--primary-gold);">الملف الشخصي للمتقدمة</h3>
          <button type="button" class="btn btn-sm btn-secondary" onclick="closeModal('candidate-dossier-modal')">✕</button>
        </div>
        <div class="modal-body" id="dossier-modal-body">
          <!-- Injected via openCandidateDossier -->
        </div>
      </div>
    </div>

    <!-- Create Period Modal -->
    <div id="create-period-modal" class="modal-backdrop">
      <div class="modal-content" style="max-width:720px;">
        <div class="modal-header">
          <h3 style="color:var(--primary-gold); display:flex; align-items:center; gap:8px;">
            <span>📅</span> إنشاء فترة خلوة جديدة بالدير
          </h3>
          <button type="button" class="btn btn-sm btn-secondary" onclick="closeModal('create-period-modal')">✕</button>
        </div>
        <form onsubmit="handleCreatePeriodSubmit(event)">
          <div class="modal-body">
            <!-- Quick Preset Durations -->
            <div class="form-group" style="margin-bottom:16px;">
              <label class="form-label" style="color:var(--text-gold);">⏱️ اختيار سريع لعدد الأيام والليالي:</label>
              <div style="display:flex; flex-wrap:wrap; gap:8px;">
                <button type="button" class="btn btn-sm btn-outline-gold" onclick="setPeriodDurationPreset(3)">
                  🌙 3 ليالي (4 أيام) - نهاية الأسبوع
                </button>
                <button type="button" class="btn btn-sm btn-secondary" onclick="setPeriodDurationPreset(4)">
                  🌙 4 ليالي (5 أيام)
                </button>
                <button type="button" class="btn btn-sm btn-secondary" onclick="setPeriodDurationPreset(5)">
                  🌙 5 ليالي (6 أيام)
                </button>
                <button type="button" class="btn btn-sm btn-secondary" onclick="setPeriodDurationPreset(7)">
                  🌙 أسبوع كامل (7 ليالي)
                </button>
              </div>
            </div>

            <!-- Start & Departure Dates -->
            <div class="grid grid-cols-2" style="margin-bottom:12px;">
              <div class="form-group">
                <label class="form-label required">📅 تاريخ الوصول / البداية (يوم-شهر-سنة)</label>
                <input type="date" id="cp-start" class="form-control" required onchange="onPeriodDateChange('start')" />
                <div id="cp-start-day-badge" style="font-size:0.82rem; color:var(--primary-gold); margin-top:4px; font-weight:600;"></div>
              </div>
              <div class="form-group">
                <label class="form-label required">🚪 تاريخ المغادرة / النهاية (يوم-شهر-سنة)</label>
                <input type="date" id="cp-dep" class="form-control" required onchange="onPeriodDateChange('dep')" />
                <div id="cp-dep-day-badge" style="font-size:0.82rem; color:var(--primary-gold); margin-top:4px; font-weight:600;"></div>
              </div>
            </div>

            <!-- Live Summary Card -->
            <div class="glass-card gold-glow" style="padding:14px 18px; margin-bottom:18px; background:rgba(212,175,55,0.08); border:1px dashed var(--primary-gold);">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <strong style="color:var(--text-gold); font-size:0.95rem;">📊 ملخص مواعيد الخلوة المحسوبة:</strong>
                <span id="cp-live-duration-badge" class="badge badge-approved" style="font-size:0.85rem;">3 ليالي (4 أيام)</span>
              </div>
              <div id="cp-live-dates-summary" style="font-size:0.88rem; color:var(--text-secondary); line-height:1.7;">
                <!-- Dynamically generated -->
              </div>
            </div>

            <div class="form-group">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <label class="form-label required" style="margin-bottom:0;">اسم الفترة المقترح</label>
                <button type="button" class="btn btn-sm btn-outline-gold" style="padding:2px 8px; font-size:0.75rem;" onclick="generateAndSetPeriodTitle()">
                  🔄 إعادة توليد الاسم تلقائياً
                </button>
              </div>
              <input type="text" id="cp-name" class="form-control" placeholder="اسم الفترة..." required />
            </div>

            <div class="grid grid-cols-2">
              <div class="form-group">
                <label class="form-label required">السعة القصوى (عدد الأسرة / النزيلات)</label>
                <input type="number" id="cp-cap" class="form-control" min="1" max="100" value="20" required />
              </div>
              <div class="form-group">
                <label class="form-label required">عدد الليالي المحسوب</label>
                <input type="number" id="cp-nights" class="form-control" min="1" max="30" value="3" required onchange="onPeriodNightsChange(this.value)" />
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">ملاحظات إدارية أو توجيهات خاصة بالفترة</label>
              <textarea id="cp-notes" class="form-control" rows="2" placeholder="مثال: خاصة بطالبات ثانوي / أو مفتوحة للجميع..."></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" onclick="closeModal('create-period-modal')">إلغاء</button>
            <button type="submit" class="btn btn-primary" style="min-width:140px;">✓ حفظ وإنشاء الفترة</button>
          </div>
        </form>
      </div>
    </div>

    <!-- WhatsApp Dispatcher Modal -->
    <div id="whatsapp-modal" class="modal-backdrop">
      <div class="modal-content">
        <div class="modal-header">
          <h3 style="color:var(--primary-gold);">إرسال رسالة WhatsApp للمتقدمة</h3>
          <button type="button" class="btn btn-sm btn-secondary" onclick="closeModal('whatsapp-modal')">✕</button>
        </div>
        <form onsubmit="handleWhatsAppSend(event)">
          <div class="modal-body">
            <input type="hidden" id="wa-profile-id" />
            <div class="form-group">
              <label class="form-label required">المستلمة</label>
              <input type="text" id="wa-recipient-name" class="form-control" readonly />
            </div>
            <div class="form-group">
              <label class="form-label required">اختر قالب الرسالة</label>
              <select id="wa-template-select" class="form-control" onchange="updateWhatsAppPreview(this.value)">
                <option value="APPROVAL">رسالة الموافقة على الخلوة</option>
                <option value="WAITLIST">رسالة الإدراج في قائمة الانتظار</option>
                <option value="REJECTION">رسالة الاعتذار عن عدم القبول</option>
                <option value="EXTENSION_APPROVED">رسالة الموافقة على طلب التمديد</option>
                <option value="ADMIN_CONTACT">رسالة طلب التواصل مع الإدارة</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">نص الرسالة</label>
              <textarea id="wa-message-body" class="form-control" rows="4"></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" onclick="closeModal('whatsapp-modal')">إلغاء</button>
            <button type="submit" class="btn btn-primary" style="background:#25D366; border-color:#25D366; color:#fff;">
              فتح وإرسال عبر WhatsApp
            </button>
          </div>
        </form>
      </div>
    </div>
  `;

  switchAdminTab('overview');
}

function togglePrivacyMode() {
  adminState.privacyMode = !adminState.privacyMode;
  showToast(`تم ${adminState.privacyMode ? 'تفعيل' : 'تعطيل'} وضع الخصوصية`, 'info');
  renderAdminDashboard(document.getElementById('main-content'));
}

async function switchAdminTab(tabKey) {
  adminState.currentTab = tabKey;
  const tabsNav = document.getElementById('admin-main-tabs');
  if (tabsNav) {
    Array.from(tabsNav.children).forEach(btn => btn.classList.remove('active'));
    event && event.target && event.target.classList.add('active');
  }

  const contentArea = document.getElementById('admin-tab-content');
  if (!contentArea) return;

  if (tabKey === 'overview') {
    await renderOverviewTab(contentArea);
  } else if (tabKey === 'periods') {
    await renderPeriodsTab(contentArea);
  } else if (tabKey === 'bookings') {
    await renderBookingsTab(contentArea);
  } else if (tabKey === 'gate') {
    await renderGateCheckinTab(contentArea);
  } else if (tabKey === 'reports') {
    await renderReportsTab(contentArea);
  } else if (tabKey === 'duplicates') {
    await renderDuplicatesAuditTab(contentArea);
  } else if (tabKey === 'staff') {
    await renderStaffTab(contentArea);
  } else if (tabKey === 'settings') {
    await renderSettingsTab(contentArea);
  }
}

// 1. Overview & Action Priorities Tab
async function renderOverviewTab(container) {
  container.innerHTML = `<p class="text-muted">جاري تحميل إحصائيات لوحة القيادة...</p>`;
  try {
    const stats = await apiCall('/admin/dashboard-stats');
    adminState.stats = stats;

    const s = stats.summary;
    const today = stats.today_actions;

    container.innerHTML = `
      <!-- Top Counter Cards -->
      <div class="grid grid-cols-4" style="gap:16px; margin-bottom:28px;">
        <div class="glass-card" style="border-right:4px solid #38BDF8;">
          <div style="font-size:0.85rem; color:var(--text-muted);">طلبات قيد المراجعة</div>
          <div style="font-size:1.8rem; font-weight:800; color:#38BDF8;">${s.under_review}</div>
          <small class="text-muted">من إجمالي ${s.total_bookings} طلب</small>
        </div>

        <div class="glass-card" style="border-right:4px solid #10B981;">
          <div style="font-size:0.85rem; color:var(--text-muted);">المقبولات المعتمدة</div>
          <div style="font-size:1.8rem; font-weight:800; color:#10B981;">${s.approved}</div>
          <small class="text-muted">حاضرات حالياً: ${s.checked_in}</small>
        </div>

        <div class="glass-card" style="border-right:4px solid #F59E0B;">
          <div style="font-size:0.85rem; color:var(--text-muted);">قائمة الانتظار</div>
          <div style="font-size:1.8rem; font-weight:800; color:#F59E0B;">${s.waiting_list}</div>
          <small class="text-muted">جاهزات للترقية</small>
        </div>

        <div class="glass-card" style="border-right:4px solid #F43F5E;">
          <div style="font-size:0.85rem; color:var(--text-muted);">تنبيهات واستثناءات عاجلة</div>
          <div style="font-size:1.8rem; font-weight:800; color:#F43F5E;">${s.urgent_alerts + s.pending_exceptions}</div>
          <small class="text-muted">تتطلب قرار الأم المسؤولة</small>
        </div>
      </div>

      <!-- Today's Action Center (Arrivals & Departures) -->
      <div class="grid grid-cols-2" style="gap:24px; margin-bottom:30px;">
        <!-- Arrivals Today -->
        <div class="glass-card gold-glow">
          <div class="section-header">
            <div class="section-title" style="font-size:1.15rem;">
              <span>🧳</span> الواصلات اليوم (${today.arrivals_count})
            </div>
            <button class="btn btn-sm btn-outline-gold" onclick="switchAdminTab('gate')">كشف البوابة</button>
          </div>
          <div style="max-height:260px; overflow-y:auto;">
            ${today.arrivals.length === 0 ? '<p class="text-muted" style="font-size:0.9rem;">لا توجد وصولات مقررة لليوم.</p>' : today.arrivals.map(a => `
              <div style="display:flex; justify-content:space-between; align-items:center; padding:10px; background:rgba(15,23,42,0.4); border-radius:8px; margin-bottom:8px;">
                <div>
                  <strong>${a.full_name}</strong>
                  <div class="text-muted" style="font-size:0.8rem;">${a.church} - ${a.diocese}</div>
                </div>
                <div style="display:flex; gap:8px;">
                  <button class="btn btn-sm btn-success" onclick="fastCheckin('${a.booking_id}')">وصلت ✓</button>
                  <button class="btn btn-sm btn-secondary" onclick="openWhatsAppModal('${a.booking_id}', '${a.full_name}')">WhatsApp</button>
                </div>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Departures Today -->
        <div class="glass-card">
          <div class="section-header">
            <div class="section-title" style="font-size:1.15rem;">
              <span>🏁</span> المغادرات اليوم (${today.departures_count})
            </div>
          </div>
          <div style="max-height:260px; overflow-y:auto;">
            ${today.departures.length === 0 ? '<p class="text-muted" style="font-size:0.9rem;">لا توجد مغادرات لليوم.</p>' : today.departures.map(d => `
              <div style="display:flex; justify-content:space-between; align-items:center; padding:10px; background:rgba(15,23,42,0.4); border-radius:8px; margin-bottom:8px;">
                <div>
                  <strong>${d.full_name}</strong>
                  <div class="text-muted" style="font-size:0.8rem;">${d.church}</div>
                </div>
                <span class="badge badge-completed">المغادرة قبل 9:00 ص</span>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<p style="color:#F43F5E;">فشل تحميل الإحصائيات.</p>`;
  }
}

// 2. Periods Management Tab
async function renderPeriodsTab(container) {
  container.innerHTML = `<p class="text-muted">جاري تحميل الفترات...</p>`;
  try {
    const periods = await apiCall('/periods/admin/all');
    adminState.periods = periods;

    container.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
        <h3 style="color:var(--primary-gold);">سجل فترات الخلوة (الحالية والقادمة والأرشيف)</h3>
        <button class="btn btn-primary" onclick="openCreatePeriodModal()">+ إنشاء فترة جديدة</button>
      </div>

      <div class="glass-card">
        <div class="table-responsive">
          <table class="custom-table">
            <thead>
              <tr>
                <th>اسم الفترة</th>
                <th>تاريخ الوصول (البداية)</th>
                <th>تاريخ المغادرة (النهاية)</th>
                <th>المدة بالأيام</th>
                <th>السعة</th>
                <th>المقبول</th>
                <th>المتبقي</th>
                <th>الحالة</th>
                <th>الإجراءات</th>
              </tr>
            </thead>
            <tbody>
              ${periods.map(p => `
                <tr>
                  <td><strong>${p.period_name}</strong></td>
                  <td>
                    <div style="font-weight:600; color:var(--text-primary);">${formatShortDate(p.start_date)}</div>
                    <div style="font-size:0.75rem; color:var(--text-muted);">${p.arrival_time_desc || '12:00 ظ'}</div>
                  </td>
                  <td>
                    <div style="font-weight:600; color:var(--text-primary);">${formatShortDate(p.departure_date)}</div>
                    <div style="font-size:0.75rem; color:var(--text-muted);">${p.departure_time_desc || 'قبل 9:00 ص'}</div>
                  </td>
                  <td>
                    <span class="badge badge-under_review" style="font-size:0.8rem;">
                      🌙 ${p.nights_count} ليالي (${p.nights_count + 1} أيام)
                    </span>
                  </td>
                  <td>${p.capacity}</td>
                  <td><span class="badge badge-approved">${p.approved_count}</span></td>
                  <td><strong style="color:var(--primary-gold);">${p.remaining_spots}</strong></td>
                  <td><span class="badge badge-${p.status.toLowerCase()}">${p.status === 'OPEN' ? 'مفتوحة للحجز' : p.status === 'FULL' ? 'مكتملة' : p.status}</span></td>
                  <td>
                    <div style="display:flex; gap:6px;">
                      <button class="btn btn-sm btn-secondary" onclick="viewPeriodWaitlist('${p.id}')">الانتظار</button>
                      <a class="btn btn-sm btn-outline-gold" href="/api/v1/reports/gate-pdf/${p.id}" target="_blank">PDF</a>
                    </div>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<p style="color:#F43F5E;">فشل تحميل الفترات.</p>`;
  }
}

// 3. Bookings Search & Filter Tab
async function renderBookingsTab(container) {
  const isCards = adminState.bookingsViewMode === 'cards';
  container.innerHTML = `
    <!-- Search & Filter Controls -->
    <div class="glass-card" style="margin-bottom:20px;">
      <div class="grid grid-cols-4" style="gap:12px; align-items:center;">
        <div class="form-group" style="grid-column: span 2; margin-bottom:0;">
          <input type="text" id="admin-search-input" class="form-control" placeholder="بحث بالاسم، الهاتف، الرقم القومي، الكنيسة، أو كود الحجز..." onkeyup="handleBookingSearch(event)" />
        </div>
        <div class="form-group" style="margin-bottom:0;">
          <select id="admin-status-filter" class="form-control" onchange="handleBookingFilter()">
            <option value="">جميع الحالات</option>
            <option value="UNDER_REVIEW">قيد المراجعة</option>
            <option value="APPROVED">مقبول</option>
            <option value="WAITING_LIST">قائمة الانتظار</option>
            <option value="REJECTED">مرفوض</option>
            <option value="CHECKED_IN">حاضرة (Checked In)</option>
            <option value="COMPLETED">مكتمل</option>
            <option value="CANCELLED">معتذرة</option>
          </select>
        </div>
        <div style="display:flex; gap:8px;">
          <button class="btn btn-primary" style="flex-grow:1;" onclick="handleBookingFilter()">تصفية 🔍</button>
          <!-- View Switcher -->
          <div style="display:flex; border:1px solid var(--border-subtle); border-radius:8px; overflow:hidden;">
            <button id="view-mode-cards-btn" class="btn btn-sm ${isCards ? 'btn-primary' : 'btn-secondary'}" style="border-radius:0; padding:6px 12px;" onclick="setBookingsViewMode('cards')" title="عرض البطاقات الذكية">🎴 بطاقات</button>
            <button id="view-mode-table-btn" class="btn btn-sm ${!isCards ? 'btn-primary' : 'btn-secondary'}" style="border-radius:0; padding:6px 12px;" onclick="setBookingsViewMode('table')" title="عرض الجدول">📑 جدول</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Bookings Container -->
    <div id="admin-bookings-table-container">
      <p class="text-muted" style="text-align:center; padding:30px;">جاري تحميل الحجوزات والبيانات...</p>
    </div>
  `;

  loadAdminBookings();
}

async function loadAdminBookings(params = {}) {
  const container = document.getElementById('admin-bookings-table-container');
  if (!container) return;

  const q = document.getElementById('admin-search-input')?.value || '';
  const status = document.getElementById('admin-status-filter')?.value || '';
  const isCards = adminState.bookingsViewMode === 'cards';

  try {
    let url = `/admin/bookings?skip=0&limit=100`;
    if (q) url += `&q=${encodeURIComponent(q)}`;
    if (status) url += `&status_filter=${status}`;

    const bookings = await apiCall(url);

    if (!bookings || bookings.length === 0) {
      container.innerHTML = `
        <div class="glass-card" style="text-align:center; padding:40px;">
          <p class="text-muted" style="font-size:1.1rem; margin-bottom:10px;">لا توجد طلبات حجوزات مطابقة للبحث أو التصفية الحالية.</p>
        </div>
      `;
      return;
    }

    const statusBadgeMap = {
      'under_review': 'badge-under_review',
      'submitted': 'badge-under_review',
      'approved': 'badge-approved',
      'rejected': 'badge-rejected',
      'waiting_list': 'badge-waiting_list',
      'checked_in': 'badge-checked_in',
      'completed': 'badge-completed',
      'cancelled': 'badge-cancelled',
      'extension_requested': 'badge-warning'
    };
    const statusArabicMap = {
      'UNDER_REVIEW': 'قيد المراجعة',
      'SUBMITTED': 'مقدم',
      'APPROVED': 'مقبول ومؤكد',
      'REJECTED': 'مرفوض',
      'WAITING_LIST': 'قائمة الانتظار',
      'CHECKED_IN': 'حاضرة بالدير',
      'COMPLETED': 'مكتمل',
      'CANCELLED': 'معتذرة',
      'EXTENSION_REQUESTED': 'طلب تمديد'
    };

    if (isCards) {
      // 🎴 Cards View (High-end responsive cards for mobile & desktop)
      container.innerHTML = `
        <div class="grid grid-cols-2" style="gap:16px;">
          ${bookings.map(b => {
            const p = b.profile || {};
            const guardians = p.guardians || [];
            const confessionFathers = p.confession_fathers || [];
            const violations = p.violations || [];
            const personalPhone = p.phone_number || '-';
            const companionPhone = p.companion_phone || '';
            const statusKey = (b.status || '').toLowerCase();
            const periodTitle = b.period ? (b.period.period_name || '-') : '-';
            const badgeClass = statusBadgeMap[statusKey] || 'badge-secondary';
            const statusLabel = statusArabicMap[b.status] || b.status || '-';
            const hasViolations = p.has_active_warning || p.is_blocked_from_booking || violations.length > 0;

            const g = guardians.length > 0 ? guardians[0] : null;
            const f = confessionFathers.length > 0 ? confessionFathers[0] : null;

            return `
              <div class="glass-card" style="padding:18px; border-radius:14px; position:relative; ${hasViolations ? 'border-color:rgba(244,63,94,0.45); background:rgba(30,20,30,0.5);' : 'border-color:rgba(212,175,55,0.25);'}">
                <!-- Card Header -->
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:14px; border-bottom:1px solid var(--border-subtle); padding-bottom:10px;">
                  <div style="display:flex; align-items:center; gap:8px;">
                    <span style="color:var(--primary-gold); font-size:1.05rem; font-weight:800; font-family:monospace; letter-spacing:0.5px;">${b.booking_reference || '-'}</span>
                    <span class="badge ${badgeClass}" style="font-size:0.78rem;">${statusLabel}</span>
                  </div>
                  <div>
                    ${hasViolations ? `
                      <a href="javascript:void(0)" onclick="openCandidateDossier('${p.id}')" class="badge badge-rejected" style="text-decoration:none; display:inline-flex; align-items:center; gap:4px; font-weight:700;">
                        ⚠️ ${violations.length > 0 ? violations.length + ' مخالفة مسجلة' : 'تنبيه سابق'}
                      </a>
                    ` : `
                      <span class="badge badge-approved" style="font-size:0.75rem;">✓ سليم (${p.total_retreats_count || 0} خلوات)</span>
                    `}
                  </div>
                </div>

                <!-- Applicant Core Info -->
                <div style="margin-bottom:14px;">
                  <div style="display:flex; justify-content:space-between; align-items:baseline; flex-wrap:wrap; gap:6px;">
                    <a href="javascript:void(0)" onclick="openCandidateDossier('${p.id}')" style="color:var(--text-primary); font-size:1.15rem; font-weight:800; text-decoration:none;">
                      👤 ${p.full_name || '-'}
                    </a>
                    <span style="font-size:0.85rem; color:var(--text-muted);">
                      ${p.birth_date ? `العمر: <strong style="color:var(--text-primary);">${calculateAge(p.birth_date)} سنة</strong>` : ''}
                      ${p.is_minor ? '<span class="badge badge-warning" style="margin-right:4px; font-size:0.7rem;">قاصر</span>' : ''}
                    </span>
                  </div>
                  <div style="display:flex; align-items:center; gap:12px; margin-top:4px; font-size:0.85rem;">
                    <span style="color:var(--primary-gold); font-family:monospace; font-weight:700;">🆔 الرقم القومي: ${p.national_id_number || 'غير مسجل'}</span>
                  </div>
                  <div style="font-size:0.85rem; color:var(--text-secondary); margin-top:4px;">
                    ⛪ ${p.church || 'الكنيسة غير محددة'} <span class="text-muted">(${p.governorate || ''} ${p.diocese ? ' - ' + p.diocese : ''})</span>
                  </div>
                </div>

                <!-- 3 Information Detail Boxes -->
                <div class="grid grid-cols-3" style="gap:10px; margin-bottom:14px; background:rgba(15,23,42,0.6); padding:12px; border-radius:10px; border:1px solid var(--border-subtle);">
                  <!-- Box 1: الرقم الشخصي -->
                  <div>
                    <div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:3px;">📱 الرقم الشخصي:</div>
                    <a href="tel:${personalPhone}" style="color:var(--primary-gold); font-weight:800; font-size:0.95rem; text-decoration:none; display:inline-block; direction:ltr;">
                      ${personalPhone}
                    </a>
                    ${companionPhone ? `<div style="font-size:0.75rem; color:var(--text-muted); margin-top:3px;">🏠 تليفون البيت: <strong style="color:var(--text-primary); direction:ltr; display:inline-block;">${companionPhone}</strong></div>` : ''}
                  </div>

                  <!-- Box 2: ولي الأمر / المسؤول -->
                  <div>
                    <div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:3px;">👨‍👩‍👧 ولي الأمر / المسؤول:</div>
                    ${g ? `
                      <div style="font-weight:700; color:var(--text-primary); font-size:0.88rem;">${g.full_name || '-'} <span class="badge badge-approved" style="padding:0px 4px; font-size:0.68rem;">${g.guardian_type || 'ولي أمر'}</span></div>
                      <a href="tel:${g.phone_number}" style="color:var(--primary-gold); font-weight:700; font-size:0.9rem; text-decoration:none; direction:ltr; display:inline-block; margin-top:2px;">
                        ${g.phone_number || '-'}
                      </a>
                    ` : (p.companion_name || p.companion_phone ? `
                      <div style="font-weight:700; color:var(--text-primary); font-size:0.88rem;">${p.companion_name || 'المسؤول'}</div>
                      <a href="tel:${p.companion_phone}" style="color:var(--primary-gold); font-weight:700; font-size:0.9rem; text-decoration:none; direction:ltr; display:inline-block; margin-top:2px;">
                        ${p.companion_phone || '-'}
                      </a>
                    ` : '<span class="text-muted" style="font-size:0.8rem;">بالغة (بدون ولي أمر)</span>')}
                  </div>

                  <!-- Box 3: أب الاعتراف -->
                  <div>
                    <div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:3px;">⛪ أب الاعتراف:</div>
                    ${f ? `
                      <div style="font-weight:700; color:#38BDF8; font-size:0.88rem;">${f.father_name || '-'}</div>
                      <a href="tel:${f.father_phone}" style="color:#38BDF8; font-weight:700; font-size:0.9rem; text-decoration:none; direction:ltr; display:inline-block; margin-top:2px;">
                        ${f.father_phone || '-'}
                      </a>
                      <div style="font-size:0.72rem; color:var(--text-muted);">${f.church_name || ''}</div>
                    ` : '<span class="text-muted" style="font-size:0.8rem;">لم يسجل</span>'}
                  </div>
                </div>

                <!-- Period Details -->
                <div style="margin-bottom:14px; font-size:0.84rem; color:var(--text-secondary); background:rgba(212,175,55,0.06); padding:8px 12px; border-radius:8px; border:1px solid rgba(212,175,55,0.15);">
                  📅 <strong>فترة الخلوة المطلوبة:</strong> ${periodTitle}
                </div>

                <!-- Actions Footer -->
                <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center; justify-content:space-between; pt-2; border-top:1px solid var(--border-subtle); padding-top:12px;">
                  <div style="display:flex; gap:8px; flex-wrap:wrap;">
                    ${b.status === 'UNDER_REVIEW' || b.status === 'SUBMITTED' ? `
                      <button class="btn btn-sm btn-success" style="font-weight:700; padding:6px 14px;" onclick="approveBookingAdmin('${b.id}')">✓ قبول الحجز</button>
                      <button class="btn btn-sm btn-danger" style="font-weight:700; padding:6px 14px;" onclick="rejectBookingAdmin('${b.id}')">✕ رفض الحجز</button>
                    ` : ''}
                    <button class="btn btn-sm btn-outline-gold" style="padding:6px 14px;" onclick="openCandidateDossier('${p.id}')">👁 فحص الملف الشامل</button>
                  </div>
                  <div>
                    <a class="btn btn-sm btn-secondary" style="color:#25D366; text-decoration:none; display:inline-flex; align-items:center; gap:4px;" href="https://wa.me/20${personalPhone.replace(/^0+/, '')}" target="_blank">
                      📲 واتساب
                    </a>
                  </div>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `;
    } else {
      // 📑 Table View (Spacious horizontal table with full phones & clean widths)
      container.innerHTML = `
        <div class="glass-card">
          <div class="table-responsive">
            <table class="custom-table" style="font-size:0.86rem; min-width:1100px;">
              <thead>
                <tr>
                  <th style="white-space:nowrap;">كود الحجز</th>
                  <th style="min-width:170px;">المتقدمة والرقم القومي</th>
                  <th style="min-width:140px; white-space:nowrap;">الرقم الشخصي</th>
                  <th style="min-width:150px;">المحافظة والكنيسة</th>
                  <th style="min-width:160px;">ولي الأمر / المسؤول</th>
                  <th style="min-width:160px;">أب الاعتراف</th>
                  <th style="white-space:nowrap;">فترة الخلوة</th>
                  <th style="white-space:nowrap;">الحالة</th>
                  <th style="white-space:nowrap;">السوابق والمشاكل</th>
                  <th style="min-width:170px; white-space:nowrap;">القرار والإجراءات</th>
                </tr>
              </thead>
              <tbody>
                ${bookings.map(b => {
                  const p = b.profile || {};
                  const guardians = p.guardians || [];
                  const confessionFathers = p.confession_fathers || [];
                  const violations = p.violations || [];
                  const personalPhone = p.phone_number || '-';
                  const companionPhone = p.companion_phone || '';
                  const statusKey = (b.status || '').toLowerCase();
                  const periodTitle = b.period ? (b.period.period_name || '-') : '-';
                  const badgeClass = statusBadgeMap[statusKey] || 'badge-secondary';
                  const statusLabel = statusArabicMap[b.status] || b.status || '-';
                  const hasViolations = p.has_active_warning || p.is_blocked_from_booking || violations.length > 0;

                  const g = guardians.length > 0 ? guardians[0] : null;
                  const f = confessionFathers.length > 0 ? confessionFathers[0] : null;

                  return `
                    <tr style="${hasViolations ? 'background:rgba(244,63,94,0.05);' : ''}">
                      <td style="white-space:nowrap;"><strong style="color:var(--primary-gold); font-family:monospace;">${b.booking_reference || '-'}</strong></td>
                      <td>
                        <a href="javascript:void(0)" onclick="openCandidateDossier('${p.id}')" style="color:var(--text-primary); font-weight:700; text-decoration:none; font-size:0.92rem;">
                          ${p.full_name || '-'}
                        </a>
                        <div style="font-size:0.75rem; color:var(--primary-gold); font-family:monospace; margin-top:2px;">
                          🆔 ${p.national_id_number || 'غير مسجل'} ${p.birth_date ? `(${calculateAge(p.birth_date)} سنة)` : ''}
                        </div>
                      </td>
                      <td>
                        <div style="direction:ltr; text-align:right;"><a href="tel:${personalPhone}" style="color:var(--primary-gold); font-weight:700; text-decoration:none;">${personalPhone}</a></div>
                        ${companionPhone ? `<div style="font-size:0.74rem; color:var(--text-muted); margin-top:2px;">🏠 <span style="direction:ltr;">${companionPhone}</span></div>` : ''}
                      </td>
                      <td>
                        <div>${p.church || '-'}</div>
                        <small class="text-muted">${p.governorate || ''} ${p.diocese ? ' - ' + p.diocese : ''}</small>
                      </td>
                      <td>
                        ${g ? `
                          <div style="font-weight:600; color:var(--text-primary);">${g.full_name || '-'} <span class="badge badge-approved" style="padding:0px 3px; font-size:0.68rem;">${g.guardian_type || 'ولي أمر'}</span></div>
                          <div style="direction:ltr; text-align:right;"><a href="tel:${g.phone_number}" style="color:var(--primary-gold); font-size:0.84rem; text-decoration:none;">${g.phone_number}</a></div>
                        ` : (p.companion_name || p.companion_phone ? `
                          <div style="font-weight:600;">${p.companion_name || 'المسؤول'}</div>
                          <div style="direction:ltr; text-align:right;"><a href="tel:${p.companion_phone}" style="color:var(--primary-gold); font-size:0.84rem; text-decoration:none;">${p.companion_phone}</a></div>
                        ` : '<span class="text-muted">-</span>')}
                      </td>
                      <td>
                        ${f ? `
                          <div style="font-weight:600; color:#38BDF8;">${f.father_name || '-'}</div>
                          <div style="direction:ltr; text-align:right;"><a href="tel:${f.father_phone}" style="color:#38BDF8; font-size:0.84rem; text-decoration:none;">${f.father_phone}</a></div>
                          <div style="font-size:0.72rem; color:var(--text-muted);">${f.church_name || ''}</div>
                        ` : '<span class="text-muted">-</span>'}
                      </td>
                      <td style="white-space:nowrap;"><span style="font-size:0.82rem;">${periodTitle}</span></td>
                      <td style="white-space:nowrap;"><span class="badge ${badgeClass}">${statusLabel}</span></td>
                      <td style="white-space:nowrap;">
                        ${hasViolations ? `
                          <a href="javascript:void(0)" onclick="openCandidateDossier('${p.id}')" class="badge badge-rejected" style="text-decoration:none; display:inline-block;" title="اضغطي لعرض تفاصيل المخالفات السابقة">
                            ⚠️ ${violations.length > 0 ? violations.length + ' مخالفة' : 'تنبيه سابق'}
                          </a>
                        ` : `
                          <span style="color:#10B981; font-size:0.82rem; font-weight:600;">
                            ✓ سليم (${p.total_retreats_count || 0} خلوة)
                          </span>
                        `}
                      </td>
                      <td style="white-space:nowrap;">
                        <div style="display:flex; gap:6px; flex-wrap:wrap; align-items:center;">
                          ${b.status === 'UNDER_REVIEW' || b.status === 'SUBMITTED' ? `
                            <button class="btn btn-sm btn-success" style="padding:4px 8px; font-size:0.8rem;" onclick="approveBookingAdmin('${b.id}')">قبول ✓</button>
                            <button class="btn btn-sm btn-danger" style="padding:4px 8px; font-size:0.8rem;" onclick="rejectBookingAdmin('${b.id}')">رفض ✕</button>
                          ` : ''}
                          ${p.id ? `<button class="btn btn-sm btn-secondary" style="padding:4px 8px; font-size:0.8rem;" onclick="openCandidateDossier('${p.id}')">👁 الملف</button>` : ''}
                        </div>
                      </td>
                    </tr>
                  `;
                }).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    }
  } catch (err) {
    console.error('Error loading admin bookings:', err);
    container.innerHTML = `<p style="color:#F43F5E;">فشل تحميل الحجوزات: ${escapeHtml(err.message || 'حدث خطأ في الاتصال')}</p>`;
  }
}

function handleBookingSearch(event) {
  if (event.key === 'Enter') {
    loadAdminBookings();
  }
}

function handleBookingFilter() {
  loadAdminBookings();
}

// 4. Candidate Full Dossier Modal
async function openCandidateDossier(profileId) {
  const modal = document.getElementById('candidate-dossier-modal');
  const body = document.getElementById('dossier-modal-body');
  const title = document.getElementById('dossier-candidate-name');

  body.innerHTML = `<p class="text-muted" style="text-align:center; padding:30px;">جاري تحميل الملف الكامل للمتقدمة وجميع البيانات المسجلة...</p>`;
  openModal('candidate-dossier-modal');

  try {
    const dossier = await apiCall(`/admin/applicant/${profileId}`);
    adminState.selectedCandidate = dossier;
    const p = dossier.profile;
    const guardians = p.guardians || [];
    const confessionFathers = p.confession_fathers || [];
    const documents = p.documents || [];
    const violations = dossier.violations || [];
    const notes = dossier.notes || [];
    const bookings = dossier.bookings || [];
    const latestBooking = bookings.length > 0 ? bookings[0] : null;

    title.innerText = `ملف المتقدمة: ${p.full_name || '-'}`;

    // Has warning / violations check
    const hasWarningsOrViolations = p.has_active_warning || p.is_blocked_from_booking || violations.length > 0 || notes.some(n => n.severity === 'CRITICAL' || n.severity === 'HIGH');

    body.innerHTML = `
      <!-- Warning / Safety Status Banner -->
      ${hasWarningsOrViolations ? `
        <div style="background:rgba(244,63,94,0.12); border:2px solid #F43F5E; border-radius:10px; padding:14px 18px; margin-bottom:20px;">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
            <div style="display:flex; align-items:center; gap:10px; color:#FDA4AF; font-weight:800; font-size:1.05rem;">
              <span style="font-size:1.3rem;">⚠️</span>
              <span>تنبيه للأم المسؤولة: توجد ملاحظات أو مخالفات سابقة مسجلة على هذه المتقدمة!</span>
            </div>
            <div style="display:flex; gap:8px;">
              <span class="badge badge-rejected" style="font-size:0.85rem;">المخالفات: ${violations.length}</span>
              <span class="badge badge-warning" style="font-size:0.85rem;">الملاحظات: ${notes.length}</span>
            </div>
          </div>
          <p style="font-size:0.88rem; color:#FECDD3; margin-top:8px; margin-bottom:0; line-height:1.6;">
            يرجى مراجعة تبويب (المخالفات والملاحظات) بالأسفل للوقوف على تفاصيل الأسباب السابقة، وللأم المسؤولة كامل الصلاحية لمنحها فرصة وقبول الحجز أو الاعتذار عنه.
          </p>
        </div>
      ` : `
        <div style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); border-radius:10px; padding:10px 16px; margin-bottom:20px; display:flex; align-items:center; justify-content:space-between;">
          <div style="display:flex; align-items:center; gap:8px; color:#34D399; font-weight:700; font-size:0.92rem;">
            <span>✓</span> السجل نظيف - لا توجد أي مخالفات أو تنبيهات سابقة مسجلة.
          </div>
          <span class="badge badge-approved" style="font-size:0.8rem;">سليم وموثق</span>
        </div>
      `}

      <!-- Quick Action & Booking Status Bar for Mother Superior -->
      ${latestBooking ? `
        <div class="glass-card gold-glow" style="padding:14px 18px; margin-bottom:20px; background:rgba(212,175,55,0.06); border:1px solid var(--primary-gold); border-radius:10px;">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
              <div style="font-size:0.85rem; color:var(--text-muted);">الحجز الحالي / الأحدث:</div>
              <strong style="color:var(--text-gold); font-size:1.05rem;">${latestBooking.period ? latestBooking.period.period_name : 'فترة الخلوة'}</strong>
              <span class="text-muted" style="margin-right:8px; font-size:0.85rem;">(كود: ${latestBooking.booking_reference})</span>
            </div>
            <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
              <span class="badge badge-${(latestBooking.status || '').toLowerCase()}" style="font-size:0.85rem;">الحالة: ${latestBooking.status}</span>
              ${(latestBooking.status === 'UNDER_REVIEW' || latestBooking.status === 'SUBMITTED') ? `
                <button class="btn btn-sm btn-success" onclick="approveBookingFromDossier('${latestBooking.id}', '${p.id}')">✓ قبول وتأكيد الحجز</button>
                <button class="btn btn-sm btn-danger" onclick="rejectBookingFromDossier('${latestBooking.id}', '${p.id}')">✕ رفض الحجز</button>
              ` : ''}
              <button class="btn btn-sm btn-outline-gold" onclick="openWhatsAppModal('${p.id}', '${p.full_name}')">
                📲 مراسلة WhatsApp
              </button>
            </div>
          </div>
        </div>
      ` : ''}

      <!-- Detailed 4-Grid Information Architecture -->
      <div class="grid grid-cols-2" style="gap:16px; margin-bottom:20px;">
        
        <!-- Card 1: Personal & Contact Details -->
        <div style="background:rgba(15,23,42,0.6); padding:16px; border-radius:10px; border:1px solid var(--border-subtle);">
          <h4 style="color:var(--primary-gold); font-size:1rem; margin-bottom:12px; display:flex; align-items:center; gap:8px;">
            <span>👤</span> البيانات الشخصية والاتصال
          </h4>
          <div style="font-size:0.88rem; line-height:2;">
            <div><strong>الاسم رباعي:</strong> <span style="color:var(--text-primary); font-weight:700;">${p.full_name || '-'}</span></div>
            <div><strong>الرقم القومي:</strong> <span style="color:var(--text-gold); font-family:monospace; font-size:0.95rem; letter-spacing:1px;">${p.national_id_number || 'غير مسجل'}</span></div>
            <div><strong>تاريخ الميلاد والعمر:</strong> ${p.birth_date ? formatShortDate(p.birth_date) : '-'} <span class="badge badge-secondary" style="font-size:0.75rem;">${calculateAge(p.birth_date)} سنة</span></div>
            <div><strong>الموبايل الشخصي:</strong> <a href="tel:${p.phone_number}" style="color:var(--primary-gold); font-weight:700;">${p.phone_number || '-'}</a></div>
            <div><strong>تليفون المنزل / المرافق:</strong> <a href="tel:${p.companion_phone || ''}" style="color:var(--text-secondary);">${p.companion_phone || '-'}</a></div>
            <div><strong>المؤهل / الوظيفة:</strong> ${p.education_or_job || '-'}</div>
            <div><strong>المحافظة:</strong> ${p.governorate || '-'} | <strong>الإيبارشية:</strong> ${p.diocese || '-'}</div>
            <div><strong>الكنيسة:</strong> ${p.church || '-'}</div>
            <div><strong>الفئة:</strong> ${p.is_minor ? '<span class="badge badge-warning" style="font-size:0.75rem;">قاصر (أقل من 21 سنة)</span>' : '<span class="badge badge-secondary" style="font-size:0.75rem;">بالغة</span>'}</div>
          </div>
        </div>

        <!-- Card 2: Guardian & Confession Father Details -->
        <div style="display:flex; flex-direction:column; gap:16px;">
          
          <!-- Guardian Box -->
          <div style="background:rgba(15,23,42,0.6); padding:14px; border-radius:10px; border:1px solid var(--border-subtle); flex-grow:1;">
            <h4 style="color:var(--primary-gold); font-size:1rem; margin-bottom:10px; display:flex; align-items:center; gap:8px;">
              <span>👨‍👩‍👧</span> بيانات ولي الأمر / المسؤول عنها
            </h4>
            ${guardians.length > 0 ? guardians.map(g => `
              <div style="background:rgba(15,23,42,0.4); padding:10px 12px; border-radius:8px; margin-bottom:6px; border-right:3px solid var(--primary-gold); font-size:0.88rem; line-height:1.8;">
                <div><strong>صلة القرابة:</strong> <span class="badge badge-approved" style="font-size:0.75rem;">${g.guardian_type || 'ولي أمر'}</span></div>
                <div><strong>اسم ولي الأمر:</strong> <span style="color:var(--text-primary); font-weight:700;">${g.full_name || '-'}</span></div>
                <div><strong>تليفون ولي الأمر:</strong> <a href="tel:${g.phone_number}" style="color:var(--primary-gold); font-weight:700;">${g.phone_number || '-'}</a></div>
              </div>
            `).join('') : `
              <div style="font-size:0.88rem; line-height:1.8;">
                ${p.companion_name || p.companion_phone ? `
                  <div><strong>اسم المرافق/المسؤول:</strong> ${p.companion_name || '-'}</div>
                  <div><strong>تليفون المرافق/المسؤول:</strong> <a href="tel:${p.companion_phone}">${p.companion_phone || '-'}</a></div>
                ` : '<p class="text-muted" style="margin:0;">لم يتم تسجيل بيانات ولي أمر مستقلة (مكتملة الأهلية).</p>'}
              </div>
            `}
          </div>

          <!-- Confession Father Box -->
          <div style="background:rgba(15,23,42,0.6); padding:14px; border-radius:10px; border:1px solid var(--border-subtle); flex-grow:1;">
            <h4 style="color:#38BDF8; font-size:1rem; margin-bottom:10px; display:flex; align-items:center; gap:8px;">
              <span>⛪</span> بيانات أب الاعتراف
            </h4>
            ${confessionFathers.length > 0 ? confessionFathers.map(f => `
              <div style="background:rgba(15,23,42,0.4); padding:10px 12px; border-radius:8px; margin-bottom:6px; border-right:3px solid #38BDF8; font-size:0.88rem; line-height:1.8;">
                <div><strong>اسم أب الاعتراف:</strong> <span style="color:#38BDF8; font-weight:700;">${f.father_name || '-'}</span></div>
                <div><strong>رقم التليفون:</strong> <a href="tel:${f.father_phone}" style="color:var(--primary-gold); font-weight:700;">${f.father_phone || '-'}</a></div>
                <div><strong>كنيسة أب الاعتراف:</strong> ${f.church_name || '-'}</div>
              </div>
            `).join('') : '<p class="text-muted" style="margin:0; font-size:0.88rem;">لم يتم تسجيل بيانات أب الاعتراف.</p>'}
          </div>

        </div>

      </div>

      <!-- Dossier Tabs Header -->
      <div class="tabs-nav" id="dossier-sub-tabs">
        <button class="tab-btn active" onclick="switchDossierTab('docs')">📁 المستندات والبطاقة (${documents.length})</button>
        <button class="tab-btn" onclick="switchDossierTab('violations')">⚠️ المخالفات السابقة (${violations.length})</button>
        <button class="tab-btn" onclick="switchDossierTab('notes')">🔒 الملاحظات السرية (${notes.length})</button>
        <button class="tab-btn" onclick="switchDossierTab('history')">📜 سجل الخلوات السابقة (${bookings.length})</button>
      </div>

      <div id="dossier-tab-content" style="margin-top:16px;">
        <!-- Injected via switchDossierTab -->
      </div>
    `;

    switchDossierTab('docs');
  } catch (err) {
    console.error(err);
    body.innerHTML = `<p style="color:#F43F5E; text-align:center; padding:20px;">فشل تحميل ملف المتقدمة: ${escapeHtml(err.message || 'حدث خطأ')}</p>`;
  }
}

async function approveBookingFromDossier(bookingId, profileId) {
  await approveBookingAdmin(bookingId);
  openCandidateDossier(profileId);
  loadAdminBookings();
}

async function rejectBookingFromDossier(bookingId, profileId) {
  await rejectBookingAdmin(bookingId);
  openCandidateDossier(profileId);
  loadAdminBookings();
}

function switchDossierTab(tabKey) {
  const d = adminState.selectedCandidate;
  if (!d) return;

  const content = document.getElementById('dossier-tab-content');
  if (!content) return;

  // Highlight active tab
  document.querySelectorAll('#dossier-sub-tabs .tab-btn').forEach(btn => btn.classList.remove('active'));
  const activeBtn = Array.from(document.querySelectorAll('#dossier-sub-tabs .tab-btn')).find(b => b.getAttribute('onclick')?.includes(`'${tabKey}'`));
  if (activeBtn) activeBtn.classList.add('active');

  const p = d.profile;
  const docs = p.documents || [];
  const violations = d.violations || [];
  const notes = d.notes || [];
  const bookings = d.bookings || [];

  if (tabKey === 'docs') {
    const docTypeArabic = {
      'NATIONAL_ID_FRONT': 'بطاقة الرقم القومي (الوجه الأمامي)',
      'NATIONAL_ID_BACK': 'بطاقة الرقم القومي (الوجه الخلفي)',
      'CONFESSION_LETTER': 'خطاب تزكية أب الاعتراف',
      'GUARDIAN_APPROVAL': 'موافقة ولي الأمر',
      'OTHER': 'مستند إضافي'
    };

    content.innerHTML = `
      <div class="grid grid-cols-2" style="gap:16px;">
        ${docs.length === 0 ? '<p class="text-muted" style="grid-column:span 2; text-align:center; padding:20px;">لم يتم رفع مستندات حتى الآن لهذه المتقدمة.</p>' : docs.map(doc => {
          const typeLabel = docTypeArabic[doc.doc_type || doc.document_type] || doc.doc_type || 'مستند';
          const sizeKb = doc.file_size_bytes ? (doc.file_size_bytes / 1024).toFixed(1) : '0';
          return `
            <div style="background:rgba(15,23,42,0.5); padding:16px; border-radius:10px; border:1px solid var(--border-subtle); display:flex; flex-direction:column; justify-content:space-between;">
              <div>
                <div style="font-weight:700; color:var(--primary-gold); margin-bottom:6px; font-size:1rem;">📄 ${typeLabel}</div>
                <div class="text-muted" style="font-size:0.82rem; margin-bottom:12px;">${doc.file_name || 'ملف مرفق'} (${sizeKb} KB)</div>
              </div>
              <a class="btn btn-sm btn-outline-gold" style="width:100%; text-align:center;" href="/api/v1/profile/document/${doc.id}" target="_blank">
                👁 استعراض وتدقيق المستند بأمان
              </a>
            </div>
          `;
        }).join('')}
      </div>
    `;
  } else if (tabKey === 'violations') {
    content.innerHTML = `
      <div style="margin-bottom:16px; display:flex; justify-content:space-between; align-items:center;">
        <span class="text-muted" style="font-size:0.9rem;">المخالفات أو المشاكل السابقة المسجلة على المتقدمة في الخلوات الماضية:</span>
        <button class="btn btn-sm btn-danger" onclick="showAddViolationForm('${p.id}')">+ تسجيل مخالفة جديدة</button>
      </div>
      <div id="add-violation-form-area" style="display:none; margin-bottom:20px; background:rgba(15,23,42,0.6); padding:16px; border-radius:10px; border:1px solid rgba(244,63,94,0.3);">
        <h4 style="color:#F43F5E; margin-bottom:10px;">تسجيل مخالفة جديدة</h4>
        <input type="text" id="new-viol-title" class="form-control" placeholder="عنوان المخالفة (مثال: عدم الالتزام بمواعيد الصلوات، إزعاج...)" style="margin-bottom:10px;" />
        <textarea id="new-viol-desc" class="form-control" rows="3" placeholder="تفاصيل المخالفة وتاريخ حدوثها..."></textarea>
        <div style="margin-top:12px; display:flex; gap:10px;">
          <button class="btn btn-sm btn-danger" onclick="saveViolation('${p.id}')">✓ حفظ المخالفة</button>
          <button class="btn btn-sm btn-secondary" onclick="document.getElementById('add-violation-form-area').style.display='none'">إلغاء</button>
        </div>
      </div>

      <div>
        ${violations.length === 0 ? `
          <div style="text-align:center; padding:30px; background:rgba(15,23,42,0.4); border-radius:10px;">
            <div style="font-size:2rem; margin-bottom:6px;">🕊️</div>
            <p style="color:#34D399; font-weight:600;">لا توجد أي مخالفات مسجلة على هذه المتقدمة.</p>
          </div>
        ` : violations.map(v => `
          <div style="background:rgba(244,63,94,0.1); padding:14px 18px; border-radius:10px; margin-bottom:10px; border-right:4px solid #F43F5E;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
              <strong style="color:#FDA4AF; font-size:1rem;">⚠️ ${v.violation_title}</strong>
              <small class="text-muted">${v.occurred_at ? v.occurred_at.slice(0,10) : ''}</small>
            </div>
            <p style="font-size:0.92rem; color:var(--text-secondary); margin-bottom:0; line-height:1.7;">${v.violation_description}</p>
          </div>
        `).join('')}
      </div>
    `;
  } else if (tabKey === 'notes') {
    content.innerHTML = `
      <div style="margin-bottom:16px; display:flex; justify-content:space-between; align-items:center;">
        <span class="text-muted" style="font-size:0.9rem;">الملاحظات السرية الخاصة بالأم المسؤولة:</span>
        <button class="btn btn-sm btn-primary" onclick="showAddNoteForm('${p.id}')">+ تسجيل ملاحظة إدارية سرية</button>
      </div>
      <div id="add-note-form-area" style="display:none; margin-bottom:20px; background:rgba(15,23,42,0.6); padding:16px; border-radius:10px; border:1px solid var(--border-subtle);">
        <h4 style="color:var(--primary-gold); margin-bottom:10px;">إضافة ملاحظة إدارية سرية جديدة</h4>
        <textarea id="new-note-content" class="form-control" rows="3" placeholder="اكتبي الملاحظة السرية هنا..."></textarea>
        <div class="grid grid-cols-2" style="margin-top:10px;">
          <div>
            <label class="form-label">مستوى الأهمية / الخطورة</label>
            <select id="new-note-severity" class="form-control">
              <option value="NORMAL">عادي (Normal)</option>
              <option value="HIGH">مهم / مرتفع (High)</option>
              <option value="CRITICAL">حرج / تحذيري (Critical)</option>
            </select>
          </div>
          <div>
            <label class="form-label">التوصية المستقبلية</label>
            <select id="new-note-rec" class="form-control">
              <option value="NONE">بدون توصية خاصة</option>
              <option value="BAN_BOOKING">منع الحجز مستقبلاً</option>
              <option value="CONDITIONAL_APPROVAL">حجز بشروط ومتابعة</option>
            </select>
          </div>
        </div>
        <div style="margin-top:12px; display:flex; gap:10px;">
          <button class="btn btn-sm btn-primary" onclick="saveAdminNote('${p.id}')">✓ حفظ الملاحظة</button>
          <button class="btn btn-sm btn-secondary" onclick="document.getElementById('add-note-form-area').style.display='none'">إلغاء</button>
        </div>
      </div>

      <div>
        ${notes.length === 0 ? '<p class="text-muted" style="text-align:center; padding:20px;">لا توجد ملاحظات إدارية سرية مسجلة.</p>' : notes.map(n => {
          const borderColor = n.severity==='CRITICAL'?'#F43F5E':n.severity==='HIGH'?'#F59E0B':'#38BDF8';
          return `
            <div style="background:rgba(15,23,42,0.5); padding:14px 18px; border-radius:10px; margin-bottom:10px; border-right:4px solid ${borderColor};">
              <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                <strong style="color:var(--text-primary); font-size:0.95rem;">${n.note_type || 'ملاحظة إدارية'} (${n.severity})</strong>
                <small class="text-muted">${n.created_at ? n.created_at.slice(0,16).replace('T', ' ') : ''}</small>
              </div>
              <p style="font-size:0.92rem; color:var(--text-secondary); margin-bottom:4px; line-height:1.7;">${n.content}</p>
              ${n.recommendation && n.recommendation !== 'NONE' ? `<div style="font-size:0.82rem; color:#F59E0B; font-weight:700;">التوصية: ${n.recommendation}</div>` : ''}
            </div>
          `;
        }).join('')}
      </div>
    `;
  } else if (tabKey === 'history') {
    content.innerHTML = `
      <div class="table-responsive">
        <table class="custom-table">
          <thead>
            <tr>
              <th>كود الحجز</th>
              <th>الفترة</th>
              <th>الحالة</th>
              <th>تاريخ التقديم</th>
            </tr>
          </thead>
          <tbody>
            ${bookings.length === 0 ? `
              <tr><td colspan="4" class="text-muted" style="text-align:center;">لا توجد حجوزات سابقة مسجلة.</td></tr>
            ` : bookings.map(b => `
              <tr>
                <td><strong>${b.booking_reference}</strong></td>
                <td>${b.period ? b.period.period_name : '-'}</td>
                <td><span class="badge badge-${(b.status || '').toLowerCase()}">${b.status}</span></td>
                <td>${b.created_at ? formatShortDate(b.created_at.slice(0,10)) : '-'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }
}

function showAddNoteForm(profId) {
  document.getElementById('add-note-form-area').style.display = 'block';
}

async function saveAdminNote(profId) {
  const content = document.getElementById('new-note-content').value;
  const severity = document.getElementById('new-note-severity').value;
  const recommendation = document.getElementById('new-note-rec').value;

  if (!content) return showToast('يرجى كتابة نص الملاحظة', 'warning');

  try {
    await apiCall('/admin-notes/notes', {
      method: 'POST',
      body: {
        profile_id: profId,
        content: content,
        severity: severity,
        recommendation: recommendation
      }
    });

    showToast('تم حفظ الملاحظة الإدارية بنجاح', 'success');
    openCandidateDossier(profId);
  } catch (err) {
    showToast(err.message || 'فشل حفظ الملاحظة', 'danger');
  }
}

function showAddViolationForm(profId) {
  document.getElementById('add-violation-form-area').style.display = 'block';
}

async function saveViolation(profId) {
  const title = document.getElementById('new-viol-title').value;
  const desc = document.getElementById('new-viol-desc').value;

  if (!title || !desc) return showToast('يرجى استكمال بيانات المخالفة', 'warning');

  try {
    await apiCall('/admin-notes/violations', {
      method: 'POST',
      body: {
        profile_id: profId,
        violation_title: title,
        violation_description: desc
      }
    });

    showToast('تم تسجيل المخالفة بنجاح', 'success');
    openCandidateDossier(profId);
  } catch (err) {
    showToast(err.message || 'فشل حفظ المخالفة', 'danger');
  }
}

// 5. Gate Reception & Check-in Tab
async function renderGateCheckinTab(container) {
  container.innerHTML = `<p class="text-muted">جاري تحميل كشوف الاستقبال للبوابة...</p>`;
  try {
    const periods = await apiCall('/periods/admin/all');
    const openPeriods = periods.filter(p => p.status !== 'CANCELLED');

    container.innerHTML = `
      <div class="glass-card" style="margin-bottom:20px;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
          <div>
            <h3 style="color:var(--primary-gold);">🚪 كشف استقبال البوابة وتسجيل الوصول</h3>
            <p class="text-muted" style="font-size:0.85rem;">تسجيل وصول النزيلات، تخصيص القلالي، وطباعة الكشوفات الورقية</p>
          </div>

          <div style="display:flex; gap:10px; align-items:center;">
            <select id="gate-period-select" class="form-control" style="width:250px;" onchange="loadGatePeriodSheet(this.value)">
              ${openPeriods.map(p => `<option value="${p.id}">${p.period_name}</option>`).join('')}
            </select>
            <button class="btn btn-outline-gold" onclick="downloadGateSheetPDF()">
              📄 طباعة / تحميل PDF
            </button>
          </div>
        </div>
      </div>

      <div class="glass-card">
        <div id="gate-sheet-table-container">
          <!-- Injected via loadGatePeriodSheet -->
        </div>
      </div>
    `;

    if (openPeriods.length > 0) {
      loadGatePeriodSheet(openPeriods[0].id);
    }
  } catch (err) {
    container.innerHTML = `<p style="color:#F43F5E;">فشل تحميل كشف الاستقبال.</p>`;
  }
}

async function loadGatePeriodSheet(periodId) {
  const container = document.getElementById('gate-sheet-table-container');
  if (!container) return;

  try {
    const items = await apiCall(`/attendance/period/${periodId}`);
    if (!items || items.length === 0) {
      container.innerHTML = `<p class="text-muted" style="text-align:center; padding:20px;">لا توجد نزيلات مقبولة مسجلة لهذه الفترة حتى الآن.</p>`;
      return;
    }

    container.innerHTML = `
      <div class="table-responsive">
        <table class="custom-table">
          <thead>
            <tr>
              <th>كود الحجز</th>
              <th>الاسم الكامل</th>
              <th>المحافظة والكنيسة</th>
              <th>رقم الهاتف</th>
              <th>حالة الحضور</th>
              <th>القلاية / الغرفة</th>
              <th>الإجراء</th>
            </tr>
          </thead>
          <tbody>
            ${items.map(item => `
              <tr>
                <td><strong>${item.booking_reference}</strong></td>
                <td><strong>${item.profile_name}</strong></td>
                <td>${item.church} - ${item.governorate}</td>
                <td>${maskPhone(item.phone_number)}</td>
                <td>
                  <span class="badge ${item.attendance_status === 'CHECKED_IN' ? 'badge-approved' : 'badge-under_review'}">
                    ${item.attendance_status === 'CHECKED_IN' ? 'حاضرة (Checked In)' : 'بانتظار الوصول'}
                  </span>
                </td>
                <td>
                  <input type="text" id="room-${item.booking_id}" class="form-control" style="width:110px; padding:6px 10px;" value="${item.room_or_cell_number || ''}" placeholder="رقم القلاية" />
                </td>
                <td>
                  ${item.attendance_status !== 'CHECKED_IN' ? `
                    <button class="btn btn-sm btn-success" onclick="confirmGateCheckin('${item.booking_id}')">
                      وصلت ✓
                    </button>
                  ` : `
                    <button class="btn btn-sm btn-secondary" onclick="updateRoomNumber('${item.booking_id}')">
                      تحديث القلاية
                    </button>
                  `}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<p style="color:#F43F5E;">فشل تحميل النزيلات.</p>`;
  }
}

async function confirmGateCheckin(bookingId) {
  const room = document.getElementById(`room-${bookingId}`)?.value || '';
  try {
    await apiCall('/attendance/check-in', {
      method: 'POST',
      body: {
        booking_id: bookingId,
        room_or_cell_number: room
      }
    });

    showToast('تم تسجيل الحضور بنجاح!', 'success');
    const periodId = document.getElementById('gate-period-select')?.value;
    if (periodId) loadGatePeriodSheet(periodId);
  } catch (err) {
    showToast(err.message || 'فشل تسجيل الحضور', 'danger');
  }
}

function downloadGateSheetPDF() {
  const periodId = document.getElementById('gate-period-select')?.value;
  if (!periodId) return;
  window.open(`/api/v1/reports/gate-pdf/${periodId}`, '_blank');
}

// Fast check-in from Overview
async function fastCheckin(bookingId) {
  try {
    await apiCall('/attendance/check-in', {
      method: 'POST',
      body: { booking_id: bookingId }
    });
    showToast('تم تسجيل الوصول بنجاح!', 'success');
    switchAdminTab('overview');
  } catch (err) {
    showToast(err.message || 'فشل تسجيل الوصول', 'danger');
  }
}

// 6. Reports & Analytics Tab
async function renderReportsTab(container) {
  container.innerHTML = `<p class="text-muted">جاري تحميل التقارير والإحصائيات...</p>`;
  try {
    const analytics = await apiCall('/reports/analytics');
    const periods = await apiCall('/periods/admin/all');

    container.innerHTML = `
      <div class="grid grid-cols-3" style="gap:20px; margin-bottom:24px;">
        <div class="glass-card">
          <div style="color:var(--text-muted); font-size:0.85rem;">إجمالي الملفات المسجلة</div>
          <div style="font-size:1.8rem; font-weight:800; color:var(--primary-gold);">${analytics.total_registered_profiles}</div>
        </div>
        <div class="glass-card">
          <div style="color:var(--text-muted); font-size:0.85rem;">الخلوات المكتملة بنجاح</div>
          <div style="font-size:1.8rem; font-weight:800; color:#10B981;">${analytics.total_completed_retreats}</div>
        </div>
        <div class="glass-card">
          <div style="color:var(--text-muted); font-size:0.85rem;">حالات عدم الحضور (No Show)</div>
          <div style="font-size:1.8rem; font-weight:800; color:#F43F5E;">${analytics.total_no_shows}</div>
        </div>
      </div>

      <!-- Breakdown Tables -->
      <div class="grid grid-cols-2" style="gap:24px;">
        <div class="glass-card">
          <h4 style="color:var(--primary-gold); margin-bottom:14px;">📍 الحجوزات حسب المحافظة</h4>
          <div class="table-responsive">
            <table class="custom-table">
              <thead><tr><th>المحافظة</th><th>عدد الحجوزات</th></tr></thead>
              <tbody>
                ${analytics.governorate_breakdown.map(g => `<tr><td>${g.governorate}</td><td><strong>${g.count}</strong></td></tr>`).join('')}
              </tbody>
            </table>
          </div>
        </div>

        <div class="glass-card">
          <h4 style="color:var(--primary-gold); margin-bottom:14px;">⛪ الحجوزات حسب الإبراشية والكنيسة</h4>
          <div class="table-responsive">
            <table class="custom-table">
              <thead><tr><th>الكنيسة</th><th>عدد الحجوزات</th></tr></thead>
              <tbody>
                ${analytics.church_breakdown.map(c => `<tr><td>${c.church}</td><td><strong>${c.count}</strong></td></tr>`).join('')}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<p style="color:#F43F5E;">فشل تحميل التقارير.</p>`;
  }
}

// 7. Staff & Supervisors Management Tab
async function renderStaffTab(container) {
  container.innerHTML = `<p class="text-muted">جاري تحميل فريق الإشراف...</p>`;
  try {
    const staffList = await apiCall('/staff');

    container.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
        <div>
          <h3 style="color:var(--primary-gold);">👥 إدارة المشرفين والصلاحيات (Granular RBAC)</h3>
          <p class="text-muted" style="font-size:0.85rem;">منح الصلاحيات الدقيقة لفريق الاستقبال والبوابة ومتابعة الحجوزات</p>
        </div>
        <button class="btn btn-primary" onclick="showCreateStaffModal()">+ إضافة مشرف جديد</button>
      </div>

      <div class="glass-card">
        <div class="table-responsive">
          <table class="custom-table">
            <thead>
              <tr>
                <th>البريد الإلكتروني</th>
                <th>الدور والصلاحية</th>
                <th>الحالة</th>
                <th>تاريخ الإنشاء</th>
              </tr>
            </thead>
            <tbody>
              ${staffList.map(s => `
                <tr>
                  <td><strong>${s.email}</strong></td>
                  <td><span class="badge badge-under_review">${s.role}</span></td>
                  <td><span class="badge ${s.is_active ? 'badge-approved' : 'badge-rejected'}">${s.is_active ? 'مفعّل' : 'معطل'}</span></td>
                  <td>${s.created_at.slice(0,10)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<p style="color:#F43F5E;">فشل تحميل المشرفين.</p>`;
  }
}

// 8. System Settings & Rules Tab
async function renderSettingsTab(container) {
  container.innerHTML = `<p class="text-muted">جاري تحميل إعدادات النظام...</p>`;
  try {
    const settings = await apiCall('/settings');

    container.innerHTML = `
      <div class="glass-card" style="max-width:750px;">
        <h3 style="color:var(--primary-gold); margin-bottom:20px;">⚙️ قواعد وسياسات بيت الخلوة القابلة للتعديل</h3>
        <form onsubmit="handleSettingsUpdate(event)">
          <div class="grid grid-cols-2">
            <div class="form-group">
              <label class="form-label required">الحد الأدنى للفاصل بين الخلوات (بالأشهر)</label>
              <input type="number" id="set-min-interval" class="form-control" min="1" max="12" value="${settings.min_booking_interval_months}" required />
            </div>
            <div class="form-group">
              <label class="form-label required">السعة الاستيعابية الافتراضية للفترة</label>
              <input type="number" id="set-cap" class="form-control" min="1" max="100" value="${settings.default_period_capacity}" required />
            </div>
          </div>

          <div class="grid grid-cols-2">
            <div class="form-group">
              <label class="form-label required">رقم WhatsApp الرسمي للدير</label>
              <input type="text" id="set-wa" class="form-control" value="${settings.whatsapp_official_number}" required />
            </div>
            <div class="form-group">
              <label class="form-label required">رقم هاتف الاستقبال والبوابة</label>
              <input type="text" id="set-phone" class="form-control" value="${settings.reception_contact_phone}" required />
            </div>
          </div>

          <button type="submit" class="btn btn-primary" style="margin-top:15px;">
            حفظ التعديلات
          </button>
        </form>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<p style="color:#F43F5E;">فشل تحميل الإعدادات.</p>`;
  }
}

async function handleSettingsUpdate(event) {
  event.preventDefault();
  const minInterval = parseInt(document.getElementById('set-min-interval').value);
  const cap = parseInt(document.getElementById('set-cap').value);
  const wa = document.getElementById('set-wa').value;
  const phone = document.getElementById('set-phone').value;

  try {
    await apiCall('/settings', {
      method: 'PUT',
      body: {
        min_booking_interval_months: minInterval,
        default_period_capacity: cap,
        whatsapp_official_number: wa,
        reception_contact_phone: phone
      }
    });

    showToast('تم تحديث قواعد وسياسات النظام بنجاح', 'success');
  } catch (err) {
    showToast(err.message || 'فشل تحديث الإعدادات', 'danger');
  }
}

// Approve / Reject Actions
async function approveBookingAdmin(bookingId) {
  try {
    await apiCall(`/admin/bookings/${bookingId}/approve`, { method: 'POST' });
    showToast('تمت الموافقة على الحجز بنجاح', 'success');
    loadAdminBookings();
  } catch (err) {
    showToast(err.message || 'فشل قبول الحجز', 'danger');
  }
}

async function rejectBookingAdmin(bookingId) {
  const reason = prompt('يرجى كتابة سبب رفض الطلب:');
  if (reason === null) return;

  try {
    await apiCall(`/admin/bookings/${bookingId}/reject`, {
      method: 'POST',
      body: { rejection_reason: reason, show_rejection_reason_to_user: true }
    });
    showToast('تم رفض الحجز وتسجيل السبب', 'info');
    loadAdminBookings();
  } catch (err) {
    showToast(err.message || 'فشل رفض الحجز', 'danger');
  }
}

// WhatsApp Dispatch Modal Helpers
function openWhatsAppModal(profileId, candidateName) {
  document.getElementById('wa-profile-id').value = profileId;
  document.getElementById('wa-recipient-name').value = candidateName;
  updateWhatsAppPreview('APPROVAL');
  openModal('whatsapp-modal');
}

function updateWhatsAppPreview(templateKey) {
  const templates = {
    'APPROVAL': 'سلام ونعمة من دير القديسة دميانة ببراري بلقاس. يسرنا إبلاغكِ بالموافقة على طلب الخلوة. موعد الوصول الساعة 12:00 ظهراً. برجاء إحضار أصل البطاقة الشخصية والأجبية والكتاب المقدس.',
    'WAITLIST': 'سلام ونعمة من بيت الخلوة بدير القديسة دميانة. تم تسجيل طلبكِ في قائمة الانتظار لاكتمال السعة. سيصلكِ إشعار فور توفر أي مكان شاغر.',
    'REJECTION': 'سلام ونعمة من دير القديسة دميانة. نعتذر عن عدم إمكانية قبول طلب الخلوة لهذه الفترة. نرجو لكِ كل البركة.',
    'EXTENSION_APPROVED': 'سلام ونعمة. تمت موافقة الأم المسؤولة على طلب تمديد فترة الخلوة الخاص بكِ.',
    'ADMIN_CONTACT': 'سلام ونعمة من إدارة بيت الخلوة بدير القديسة دميانة. نرجو التواصل معنا للأهمية بخصوص حجزكِ.'
  };
  document.getElementById('wa-message-body').value = templates[templateKey] || '';
}

async function handleWhatsAppSend(event) {
  event.preventDefault();
  const profileId = document.getElementById('wa-profile-id').value;
  const templateKey = document.getElementById('wa-template-select').value;
  const customMsg = document.getElementById('wa-message-body').value;

  try {
    const res = await apiCall('/communication/send-whatsapp', {
      method: 'POST',
      body: {
        profile_id: profileId,
        template_name: templateKey,
        custom_message: customMsg
      }
    });

    closeModal('whatsapp-modal');
    showToast('تم تسجيل الرسالة وتوليد رابط الإرسال', 'success');
    window.open(res.direct_link, '_blank');
  } catch (err) {
    showToast(err.message || 'فشل إرسال الرسالة', 'danger');
  }
}

// ==============================================================================
// Interactive Period Creation Controller & Day-Based Helpers
// ==============================================================================
function openCreatePeriodModal() {
  openModal('create-period-modal');

  // Initialize start date to tomorrow if not set
  const today = new Date();
  today.setDate(today.getDate() + 1);
  const tomorrowStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  
  const startInput = document.getElementById('cp-start');
  const depInput = document.getElementById('cp-dep');
  const nightsInput = document.getElementById('cp-nights');
  
  if (startInput) startInput.value = tomorrowStr;
  if (nightsInput) nightsInput.value = 3;
  if (depInput) depInput.value = addDaysToDate(tomorrowStr, 3);
  
  updatePeriodModalLivePreview();
}

function setPeriodDurationPreset(nights) {
  const startInput = document.getElementById('cp-start');
  const depInput = document.getElementById('cp-dep');
  const nightsInput = document.getElementById('cp-nights');
  
  const startDate = startInput?.value || addDaysToDate(new Date().toISOString().split('T')[0], 1);
  if (nightsInput) nightsInput.value = nights;
  if (depInput) depInput.value = addDaysToDate(startDate, nights);
  
  updatePeriodModalLivePreview();
}

function onPeriodDateChange(changedField) {
  const startInput = document.getElementById('cp-start');
  const depInput = document.getElementById('cp-dep');
  const nightsInput = document.getElementById('cp-nights');

  if (changedField === 'start') {
    const nights = parseInt(nightsInput?.value || '3', 10);
    if (startInput?.value && depInput) {
      depInput.value = addDaysToDate(startInput.value, nights);
    }
  } else if (changedField === 'dep') {
    if (startInput?.value && depInput?.value) {
      const diff = calculateDateDifference(startInput.value, depInput.value);
      if (diff > 0 && nightsInput) {
        nightsInput.value = diff;
      }
    }
  }

  updatePeriodModalLivePreview();
}

function onPeriodNightsChange(nightsVal) {
  const startInput = document.getElementById('cp-start');
  const depInput = document.getElementById('cp-dep');
  const nights = parseInt(nightsVal, 10) || 1;

  if (startInput?.value && depInput) {
    depInput.value = addDaysToDate(startInput.value, nights);
  }

  updatePeriodModalLivePreview();
}

function updatePeriodModalLivePreview() {
  const startVal = document.getElementById('cp-start')?.value;
  const depVal = document.getElementById('cp-dep')?.value;
  const nightsVal = parseInt(document.getElementById('cp-nights')?.value || '3', 10);
  const capVal = document.getElementById('cp-cap')?.value || '20';

  const startBadge = document.getElementById('cp-start-day-badge');
  const depBadge = document.getElementById('cp-dep-day-badge');
  const durationBadge = document.getElementById('cp-live-duration-badge');
  const summaryDiv = document.getElementById('cp-live-dates-summary');

  if (startBadge) startBadge.innerText = startVal ? `يوم الوصول: ${formatArabicDate(startVal)}` : '';
  if (depBadge) depBadge.innerText = depVal ? `يوم المغادرة: ${formatArabicDate(depVal)}` : '';

  const totalDays = nightsVal + 1;
  if (durationBadge) durationBadge.innerText = `🌙 ${nightsVal} ليالي (${totalDays} أيام)`;

  if (summaryDiv && startVal && depVal) {
    summaryDiv.innerHTML = `
      <div>📅 <strong>الوصول (البدء):</strong> ${formatArabicDate(startVal)} (12:00 ظهراً)</div>
      <div>🚪 <strong>المغادرة (الانتهاء):</strong> ${formatArabicDate(depVal)} (قبل 9:00 صباحاً)</div>
      <div>🛏️ <strong>السعة المتاحة:</strong> ${capVal} سرير / نزيلة</div>
    `;
  }

  generateAndSetPeriodTitle();
}

function generateAndSetPeriodTitle() {
  const startVal = document.getElementById('cp-start')?.value;
  const depVal = document.getElementById('cp-dep')?.value;
  const nightsVal = parseInt(document.getElementById('cp-nights')?.value || '3', 10);
  const nameInput = document.getElementById('cp-name');

  if (startVal && depVal && nameInput) {
    const startShort = formatDayMonthOnly(startVal);
    const depShort = formatDayMonthOnly(depVal);
    nameInput.value = `فترة خلوة: من ${startShort} إلى ${depShort} (${nightsVal} ليالي)`;
  }
}

async function handleCreatePeriodSubmit(event) {
  event.preventDefault();
  const name = document.getElementById('cp-name').value.trim();
  const start = document.getElementById('cp-start').value;
  const dep = document.getElementById('cp-dep').value;
  const cap = parseInt(document.getElementById('cp-cap').value, 10);
  const nights = parseInt(document.getElementById('cp-nights').value, 10);
  const notes = document.getElementById('cp-notes').value.trim();

  if (!start || !dep) {
    showToast('يرجى تحديد تاريخ البداية وتاريخ المغادرة', 'warning');
    return;
  }

  try {
    await apiCall('/periods', {
      method: 'POST',
      body: {
        period_name: name,
        start_date: start,
        end_date: dep,
        departure_date: dep,
        capacity: cap,
        nights_count: nights,
        admin_notes: notes
      }
    });

    closeModal('create-period-modal');
    showToast(`تم إنشاء فترة الخلوة (${name}) بنجاح!`, 'success');
    if (adminState.currentTab === 'periods') switchAdminTab('periods');
    else switchAdminTab('overview');
  } catch (err) {
    showToast(err.message || 'فشل إنشاء الفترة', 'danger');
  }
}

// ------------------------------------------------------------------------------
// Waitlist Management Modal & Handlers
// ------------------------------------------------------------------------------
async function viewPeriodWaitlist(periodId) {
  let modal = document.getElementById('period-waitlist-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'period-waitlist-modal';
    modal.className = 'modal-backdrop';
    document.body.appendChild(modal);
  }

  modal.innerHTML = `
    <div class="modal-content" style="max-width:780px;">
      <div class="modal-header">
        <h3 style="color:var(--primary-gold);">⏳ قائمة الانتظار للفترة</h3>
        <button type="button" class="btn btn-sm btn-secondary" onclick="closeModal('period-waitlist-modal')">✕</button>
      </div>
      <div class="modal-body" id="waitlist-modal-body">
        <p class="text-muted">جاري تحميل قائمة الانتظار...</p>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" onclick="closeModal('period-waitlist-modal')">إغلاق</button>
      </div>
    </div>
  `;

  openModal('period-waitlist-modal');
  const body = document.getElementById('waitlist-modal-body');

  try {
    const items = await apiCall(`/periods/${periodId}/waitlist`);
    if (!items || items.length === 0) {
      body.innerHTML = `<p class="text-muted" style="text-align:center; padding:20px;">لا توجد طلبات في قائمة الانتظار لهذه الفترة حالياً.</p>`;
      return;
    }

    body.innerHTML = `
      <div class="table-responsive">
        <table class="custom-table">
          <thead>
            <tr>
              <th>الترتيب</th>
              <th>الاسم</th>
              <th>المحافظة والكنيسة</th>
              <th>رقم الهاتف</th>
              <th>تاريخ التقديم</th>
              <th>الإجراء</th>
            </tr>
          </thead>
          <tbody>
            ${items.map(it => `
              <tr>
                <td><span class="badge badge-waiting_list">#${it.queue_number}</span></td>
                <td><strong>${it.profile_name}</strong></td>
                <td>${it.church || '-'} (${it.governorate || '-'})</td>
                <td>${maskPhone(it.profile_phone)}</td>
                <td>${it.created_at ? it.created_at.slice(0, 10) : '-'}</td>
                <td>
                  <button class="btn btn-sm btn-success" onclick="promoteWaitlistUser('${it.id}', '${periodId}')">
                    ترقية وقبول ✓
                  </button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (err) {
    body.innerHTML = `<p style="color:#F43F5E;">فشل تحميل قائمة الانتظار: ${err.message || ''}</p>`;
  }
}

async function promoteWaitlistUser(waitlistId, periodId) {
  if (!confirm('هل ترغبين في ترقية هذه المتقدمة من قائمة الانتظار وقبول حجزها في الفترة؟')) return;

  try {
    await apiCall(`/admin/waitlist/${waitlistId}/promote`, { method: 'POST' });
    showToast('تمت ترقية الحجز وقبوله بنجاح!', 'success');
    viewPeriodWaitlist(periodId);
    if (adminState.currentTab === 'periods') switchAdminTab('periods');
    if (adminState.currentTab === 'overview') switchAdminTab('overview');
  } catch (err) {
    showToast(err.message || 'فشل ترقية الطلب', 'danger');
  }
}

// ------------------------------------------------------------------------------
// Gate Room / Cell Number Update
// ------------------------------------------------------------------------------
async function updateRoomNumber(bookingId) {
  const room = document.getElementById(`room-${bookingId}`)?.value || '';
  try {
    await apiCall('/attendance/check-in', {
      method: 'POST',
      body: {
        booking_id: bookingId,
        room_or_cell_number: room
      }
    });
    showToast('تم تحديث رقم القلاية/الغرفة بنجاح!', 'success');
  } catch (err) {
    showToast(err.message || 'فشل تحديث رقم القلاية', 'danger');
  }
}

// ------------------------------------------------------------------------------
// Staff & Supervisors Management Modal
// ------------------------------------------------------------------------------
function showCreateStaffModal() {
  let modal = document.getElementById('create-staff-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'create-staff-modal';
    modal.className = 'modal-backdrop';
    document.body.appendChild(modal);
  }

  modal.innerHTML = `
    <div class="modal-content">
      <div class="modal-header">
        <h3 style="color:var(--primary-gold);">+ إضافة حساب مشرف / مسؤولة جديد</h3>
        <button type="button" class="btn btn-sm btn-secondary" onclick="closeModal('create-staff-modal')">✕</button>
      </div>
      <form onsubmit="handleCreateStaffSubmit(event)">
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label required">البريد الإلكتروني</label>
            <input type="email" id="cs-email" class="form-control" placeholder="supervisor@stdemiana.org" required dir="ltr" />
          </div>
          <div class="form-group">
            <label class="form-label required">كلمة المرور</label>
            <div class="password-input-wrapper">
              <input type="password" id="cs-pass" class="form-control" placeholder="••••••••" required minlength="8" />
              <button type="button" class="btn-toggle-password" onclick="togglePasswordVisibility('cs-pass', this)" title="إظهار/إخفاء كلمة المرور">
                👁️
              </button>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label required">الدور الوظيفي / الصلاحية</label>
            <select id="cs-role" class="form-control" required>
              <option value="BOOKING_SUPERVISOR">مشرفة مراجعة الحجوزات (Booking Supervisor)</option>
              <option value="RECEPTION_SUPERVISOR">مشرفة الاستقبال والبوابة (Reception Supervisor)</option>
              <option value="REPORT_SUPERVISOR">مشرفة التقارير والإحصائيات (Report Supervisor)</option>
              <option value="CUSTOM_STAFF">عضو فريق خدمة بيت الخلوة (General Staff)</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" onclick="closeModal('create-staff-modal')">إلغاء</button>
          <button type="submit" class="btn btn-primary">إنشاء الحساب</button>
        </div>
      </form>
    </div>
  `;

  openModal('create-staff-modal');
}

async function handleCreateStaffSubmit(event) {
  event.preventDefault();
  const email = document.getElementById('cs-email').value.trim();
  const password = document.getElementById('cs-pass').value;
  const role = document.getElementById('cs-role').value;

  try {
    await apiCall('/staff', {
      method: 'POST',
      body: { email, password, role }
    });

    closeModal('create-staff-modal');
    showToast('تم إنشاء حساب المشرفة بنجاح!', 'success');
    if (adminState.currentTab === 'staff') switchAdminTab('staff');
  } catch (err) {
    showToast(err.message || 'فشل إنشاء حساب المشرف', 'danger');
  }
}

// 8. Duplicates & Correlation Audit Tab
async function renderDuplicatesAuditTab(container) {
  container.innerHTML = `<p class="text-muted">جاري فحص وتدقيق السجلات وقواعد البيانات لكشف أي تشابه أو تكرار...</p>`;
  try {
    const res = await apiCall('/admin/duplicates/audit');
    const items = res.audit_items || [];

    let itemsHtml = '';
    if (items.length === 0) {
      itemsHtml = `
        <div style="text-align:center; padding:40px;" class="glass-card">
          <div style="font-size:3rem; color:#10B981; margin-bottom:10px;">✓</div>
          <h3 style="color:#10B981;">النظام نظيف تماماً من أي حسابات أو بيانات مكررة</h3>
          <p class="text-muted">لم يتم رصد أي اشتراك مريب في أرقام الهواتف أو تطابق في الهويات بين المتقدمات.</p>
        </div>
      `;
    } else {
      itemsHtml = items.map(item => `
        <div class="glass-card" style="margin-bottom:18px; border-right:4px solid #F59E0B;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <div>
              <strong style="color:var(--primary-gold); font-size:1.05rem;">⚠️ ${item.label}</strong>
              <span class="badge badge-under_review" style="margin-right:8px;">${item.count} حسابات متطابقة</span>
            </div>
          </div>
          <table class="table" style="font-size:0.85rem;">
            <thead>
              <tr>
                <th>اسم المتقدمة</th>
                <th>الهاتف</th>
                <th>الرقم القومي</th>
                <th>المحافظة / الكنيسة</th>
                <th>تاريخ التسجيل</th>
                <th>إجراءات</th>
              </tr>
            </thead>
            <tbody>
              ${item.profiles.map(p => `
                <tr>
                  <td><strong>${p.full_name}</strong></td>
                  <td>${maskPhone(p.phone_number)}</td>
                  <td>${p.national_id || '<span class="text-muted">غير مدخل</span>'}</td>
                  <td>${p.governorate} – ${p.church}</td>
                  <td>${p.created_at}</td>
                  <td>
                    <button class="btn btn-sm btn-outline-gold" onclick="openCandidateDossier('${p.id}')">
                      عرض الملف الكامل
                    </button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `).join('');
    }

    container.innerHTML = `
      <div class="section-header">
        <div class="section-title">
          <span>🛡️</span> منظومة التدقيق ومنع تكرار الحسابات
        </div>
        <button class="btn btn-sm btn-outline-gold" onclick="switchAdminTab('duplicates')">
          🔄 إعادة الفحص الآن
        </button>
      </div>

      <div class="alert-spiritual" style="margin-bottom:20px;">
        💡 يراقب هذا المحرك الذكي أي محاولات لتكرار التسجيل أو استخدام نفس أرقام الهواتف أو تشابه الأسماء والبيانات لتفادي الازدواجية وضمان عدالة توزيع فترات الخلوة.
      </div>

      <div>
        ${itemsHtml}
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<p class="text-danger">فشل تحميل تقرير تدقيق التكرار: ${err.message}</p>`;
  }
}


