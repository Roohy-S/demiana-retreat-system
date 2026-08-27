/**
 * Applicant / Guest Dashboard View
 */

async function renderGuestDashboard(container) {
  container.innerHTML = `
    <div class="container" style="padding-top:30px; padding-bottom:80px;">
      <!-- Welcome Header -->
      <div class="section-header">
        <div>
          <h1 style="color:var(--primary-gold); font-size:1.8rem; display:flex; align-items:center; gap:10px;">
            <span>✝</span> لوحة متابعة الخلوة الخاصة بي
          </h1>
          <p class="text-muted" style="font-size:0.9rem;">بيت الخلوة بدير القديسة دميانة ببراري بلقاس</p>
        </div>
        <button class="btn btn-sm btn-primary" onclick="openNewBookingModal()">
          <span>+</span> حجز فترة جديدة
        </button>
      </div>

      <!-- Dashboard Content Grid -->
      <div class="grid grid-cols-3" style="gap:24px;">
        <!-- Main Column (Active Booking & History) -->
        <div style="grid-column: span 2;">
          <!-- Active Booking Status Card -->
          <div id="guest-active-booking-card" class="glass-card gold-glow" style="margin-bottom:24px;">
            <p>جاري تحميل بيانات الحجز...</p>
          </div>

          <!-- All Bookings History -->
          <div class="glass-card" style="margin-bottom:24px;">
            <h3 style="color:var(--primary-gold); margin-bottom:16px; font-size:1.2rem;">
              📜 سجل الحجوزات السابقة
            </h3>
            <div id="guest-bookings-history-list">
              <p class="text-muted">جاري تحميل السجل...</p>
            </div>
          </div>
        </div>

        <!-- Sidebar (Profile & Notifications) -->
        <div>
          <!-- In-App Notifications Card -->
          <div class="glass-card" style="margin-bottom:24px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
              <h3 style="color:var(--primary-gold); font-size:1.15rem;">🔔 الإشعارات</h3>
              <button class="btn btn-sm btn-secondary" onclick="markAllNotificationsRead()">تحديد الكل كمقروء</button>
            </div>
            <div id="guest-notifications-list" style="max-height:280px; overflow-y:auto;">
              <p class="text-muted">لا توجد إشعارات جديدة.</p>
            </div>
          </div>

          <!-- Profile Snapshot Card -->
          <div id="guest-profile-card" class="glass-card">
            <p>جاري تحميل الملف الشخصي...</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Extension Request Modal -->
    <div id="extension-modal" class="modal-backdrop">
      <div class="modal-content">
        <div class="modal-header">
          <h3 style="color:var(--primary-gold);">طلب تمديد مدة الخلوة</h3>
          <button type="button" class="btn btn-sm btn-secondary" onclick="closeModal('extension-modal')">✕</button>
        </div>
        <form onsubmit="handleExtensionSubmit(event)">
          <div class="modal-body">
            <input type="hidden" id="ext-booking-id" />
            <div class="form-group">
              <label class="form-label required">عدد الأيام الإضافية المطلوبة</label>
              <input type="number" id="ext-days" class="form-control" min="1" max="3" value="1" required />
            </div>
            <div class="form-group">
              <label class="form-label required">سبب طلب التمديد (مختصر)</label>
              <input type="text" id="ext-reason" class="form-control" placeholder="مثال: بعد المسافة والمواصلات من الصعيد" required />
            </div>
            <div class="form-group">
              <label class="form-label">شرح تفصيلي للظروف</label>
              <textarea id="ext-details" class="form-control" rows="3" placeholder="اشرحي بالتفصيل للأم المسؤولة..."></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" onclick="closeModal('extension-modal')">إلغاء</button>
            <button type="submit" class="btn btn-primary">إرسال طلب التمديد</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Quick New Booking Modal for Logged-in Guest -->
    <div id="new-booking-modal" class="modal-backdrop">
      <div class="modal-content" style="max-width:650px;">
        <div class="modal-header">
          <h3 style="color:var(--primary-gold);">✝ حجز فترة خلوة جديدة</h3>
          <button type="button" class="btn btn-sm btn-secondary" onclick="closeModal('new-booking-modal')">✕</button>
        </div>
        <form onsubmit="handleQuickBookingSubmit(event)">
          <div class="modal-body">
            <p class="text-muted" style="font-size:0.9rem; margin-bottom:15px;">
              اختاري إحدى الفترات المفتوحة التالية للحجز الفوري ببيانات ملفكِ المسجل:
            </p>
            <div id="quick-booking-periods-container" style="display:flex; flex-direction:column; gap:10px; max-height:280px; overflow-y:auto; margin-bottom:15px;">
              <p class="text-muted">جاري تحميل الفترات المتاحة...</p>
            </div>
            <div style="margin-top:15px; padding-top:12px; border-top:1px dashed var(--border-subtle);">
              <label style="display:flex; align-items:center; gap:8px; cursor:pointer;">
                <input type="checkbox" id="quick-exc-check" onchange="document.getElementById('quick-exc-box').style.display = this.checked ? 'block' : 'none'" />
                <span style="font-size:0.85rem; color:var(--primary-gold); font-weight:600;">طلب استثناء فاصل زمني (أقل من 3 أشهر من آخر خلوة)</span>
              </label>
              <div id="quick-exc-box" style="display:none; margin-top:8px;">
                <textarea id="quick-exc-reason" class="form-control" rows="2" placeholder="اكتبي سبب طلب الاستثناء للأم المسؤولة..."></textarea>
              </div>
            </div>
            <div style="margin-top:12px;">
              <label style="display:flex; align-items:center; gap:8px; cursor:pointer;">
                <input type="checkbox" id="quick-rules-agree" checked required />
                <span style="font-size:0.85rem;">أتعهد بالالتزام بلائحة وقوانين بيت الخلوة بالدير.</span>
              </label>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" onclick="closeModal('new-booking-modal')">إلغاء</button>
            <button type="submit" class="btn btn-primary">تأكيد إرسال طلب الحجز</button>
          </div>
        </form>
      </div>
    </div>
  `;

  loadGuestDashboardData();
}

async function openNewBookingModal() {
  openModal('new-booking-modal');
  const container = document.getElementById('quick-booking-periods-container');
  if (!container) return;

  try {
    const periods = await apiCall('/periods');
    if (!periods || periods.length === 0) {
      container.innerHTML = `<p class="text-muted">لا توجد فترات خلوة معلنة حالياً. يرجى مراجعة إدارة الدير.</p>`;
      return;
    }

    container.innerHTML = periods.map((p, idx) => {
      const isFull = p.status === 'FULL' || p.remaining_spots <= 0;
      return `
        <label class="glass-card" style="display:flex; align-items:center; gap:12px; padding:12px; cursor:pointer; margin-bottom:6px;">
          <input type="radio" name="quick-period-radio" value="${p.id}" ${idx === 0 ? 'checked' : ''} required />
          <div style="flex:1;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <strong style="color:var(--text-light); font-size:0.95rem;">${p.period_name}</strong>
              <span class="badge badge-${p.status.toLowerCase()}">${isFull ? 'مكتملة (انتظار)' : `متاح ${p.remaining_spots} مكان`}</span>
            </div>
            <div class="text-muted" style="font-size:0.8rem; margin-top:3px;">
              📅 البدء: ${p.start_date} (${p.arrival_time_desc}) ➔ المغادرة: ${p.departure_date} (${p.departure_time_desc})
            </div>
          </div>
        </label>
      `;
    }).join('');
  } catch (err) {
    container.innerHTML = `<p style="color:#F43F5E;">فشل تحميل الفترات المتاحة.</p>`;
  }
}

async function handleQuickBookingSubmit(event) {
  event.preventDefault();
  const selectedRadio = document.querySelector('input[name="quick-period-radio"]:checked');
  if (!selectedRadio) {
    showToast('يرجى اختيار فترة الخلوة المطلوبة', 'warning');
    return;
  }

  const periodId = selectedRadio.value;
  const hasExc = document.getElementById('quick-exc-check')?.checked || false;
  const excReason = document.getElementById('quick-exc-reason')?.value?.trim() || '';
  const agreed = document.getElementById('quick-rules-agree')?.checked || false;

  if (!agreed) {
    showToast('يجب الموافقة على لائحة بيت الخلوة', 'warning');
    return;
  }

  try {
    const res = await apiCall('/bookings/submit', {
      method: 'POST',
      body: {
        period_id: periodId,
        agreed_to_rules: agreed,
        has_interval_exception: hasExc,
        interval_exception_reason: excReason
      }
    });

    closeModal('new-booking-modal');
    showToast(`تم تقديم طلب الخلوة بنجاح! رقم الحجز: ${res.booking_reference}`, 'success');
    loadGuestDashboardData();
  } catch (err) {
    showToast(err.message || 'فشل تقديم طلب الحجز', 'danger');
  }
}

async function loadGuestDashboardData() {
  // Load My Bookings
  try {
    const bookings = await apiCall('/bookings/my');
    const activeCard = document.getElementById('guest-active-booking-card');
    const historyList = document.getElementById('guest-bookings-history-list');

    if (!bookings || bookings.length === 0) {
      activeCard.innerHTML = `
        <div style="text-align:center; padding:30px 20px;">
          <div style="font-size:3rem; margin-bottom:10px;">📅</div>
          <h3 style="color:var(--text-gold); margin-bottom:8px;">لا يوجد حجز خلوة نشط حالياً</h3>
          <p class="text-muted" style="margin-bottom:20px;">يمكنكِ اختيار إحدى الفترات المفتوحة والتقدم بطلب خلوة جديد.</p>
          <button class="btn btn-primary" onclick="navigate('register_wizard')">تقديم طلب خلوة جديد</button>
        </div>
      `;
      historyList.innerHTML = `<p class="text-muted">لا توجد حجوزات سابقة مسجلة.</p>`;
    } else {
      const latest = bookings[0];
      const p = latest.period || {};
      
      // Status badge and explanation text
      let statusBadge = '';
      let statusDesc = '';
      
      if (latest.status === 'UNDER_REVIEW' || latest.status === 'SUBMITTED') {
        statusBadge = '<span class="badge badge-under_review">قيد المراجعة الإدارية</span>';
        statusDesc = 'تم استلام طلبكِ وجاري مراجعته من قبل إدارة بيت الخلوة بالدير.';
      } else if (latest.status === 'APPROVED') {
        statusBadge = '<span class="badge badge-approved">تمت الموافقة على الخلوة</span>';
        statusDesc = 'بركة القديسة دميانة. تمت الموافقة على حجزكِ! يرجى الالتزام بموعد الوصول وإحضار أصل البطاقة وجواب أب الاعتراف.';
      } else if (latest.status === 'WAITING_LIST') {
        statusBadge = '<span class="badge badge-waiting_list">في قائمة الانتظار</span>';
        statusDesc = 'الفترة مكتملة العدد حالياً. تم وضعكِ في قائمة الانتظار وسيتم إشعاركِ فور توفر أي مكان شاغر.';
      } else if (latest.status === 'CHECKED_IN') {
        statusBadge = '<span class="badge badge-checked_in">حاضرة بالدير (Checked In)</span>';
        statusDesc = 'خلوة مباركة وممتلئة بالسلام والنعمة.';
      } else if (latest.status === 'COMPLETED') {
        statusBadge = '<span class="badge badge-completed">اكتملت الخلوة</span>';
        statusDesc = 'تمت فترة الخلوة بسلام ونعمة المسيح.';
      } else if (latest.status === 'REJECTED') {
        statusBadge = '<span class="badge badge-rejected">نعتذر، لم تتم الموافقة</span>';
        statusDesc = latest.show_rejection_reason_to_user && latest.rejection_reason ? `سبب الاعتذار: ${latest.rejection_reason}` : 'نعتذر عن عدم إمكانية قبول الطلب لهذه الفترة.';
      } else if (latest.status === 'CANCELLED') {
        statusBadge = '<span class="badge badge-cancelled">تم إلغاء الحجز</span>';
        statusDesc = 'تم تسجيل اعتذاركِ عن موعد الخلوة.';
      } else if (latest.status === 'EXTENSION_REQUESTED') {
        statusBadge = '<span class="badge badge-extension_requested">طلب تمديد قيد المراجعة</span>';
        statusDesc = 'تم إرسال طلب تمديد مدة الإقامة وهو الآن بانتظار قرار الأم المسؤولة.';
      } else if (latest.status === 'EXTENSION_APPROVED') {
        statusBadge = '<span class="badge badge-approved">تمت الموافقة على التمديد</span>';
        statusDesc = 'تمت الموافقة على مدة الإقامة الإضافية.';
      }

      activeCard.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px;">
          <div>
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
              <h2 style="color:var(--primary-gold); font-size:1.35rem;">${p.period_name || 'فترة الخلوة'}</h2>
              ${statusBadge}
            </div>
            <div style="font-size:0.9rem; color:var(--text-muted);">
              كود الحجز المرجعي: <strong style="color:var(--text-primary);">${latest.booking_reference}</strong>
            </div>
          </div>
        </div>

        <div style="background:rgba(15,23,42,0.6); padding:16px; border-radius:10px; border-right:4px solid var(--primary-gold); margin-bottom:20px;">
          <p style="font-size:1rem; color:var(--text-gold); line-height:1.7;">${statusDesc}</p>
        </div>

        <div class="grid grid-cols-3" style="gap:14px; margin-bottom:20px; font-size:0.9rem; line-height:1.8;">
          <div style="background:rgba(15,23,42,0.4); padding:12px; border-radius:8px;">
            <div>📅 <strong>الوصول:</strong> ${p.start_date || '-'}</div>
            <small class="text-muted">(${p.arrival_time_desc || '12:00 ظهراً'})</small>
          </div>
          <div style="background:rgba(15,23,42,0.4); padding:12px; border-radius:8px;">
            <div>🏁 <strong>المغادرة:</strong> ${p.departure_date || '-'}</div>
            <small class="text-muted">(${p.departure_time_desc || 'قبل 9:00 صباحاً'})</small>
          </div>
          <div style="background:rgba(15,23,42,0.4); padding:12px; border-radius:8px;">
            <div>🌙 <strong>المدة:</strong> ${p.nights_count || 3} ليالٍ</div>
            <small class="text-muted">اليوم الرابع يوم المغادرة</small>
          </div>
        </div>

        <div style="display:flex; gap:10px; flex-wrap:wrap; border-top:1px solid var(--border-subtle); padding-top:16px;">
          ${(latest.status === 'APPROVED' || latest.status === 'CHECKED_IN') ? `
            <button class="btn btn-sm btn-outline-gold" onclick="openExtensionModal('${latest.id}')">
              ⏳ طلب تمديد مدة الخلوة
            </button>
          ` : ''}
          ${(latest.status === 'APPROVED' || latest.status === 'UNDER_REVIEW' || latest.status === 'WAITING_LIST') ? `
            <button class="btn btn-sm btn-danger" onclick="cancelMyBooking('${latest.id}')">
              ✕ اعتذار عن الحجز
            </button>
          ` : ''}
        </div>
      `;

      // Render History
      historyList.innerHTML = bookings.map(b => `
        <div style="display:flex; justify-content:space-between; align-items:center; padding:12px 14px; background:rgba(15,23,42,0.4); border-radius:8px; margin-bottom:8px;">
          <div>
            <strong style="color:var(--text-primary); font-size:0.95rem;">${b.booking_reference}</strong>
            <span class="text-muted" style="margin-right:8px; font-size:0.85rem;">- ${b.period ? b.period.period_name : ''}</span>
          </div>
          <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:0.8rem; color:var(--text-muted);">${b.created_at ? b.created_at.slice(0,10) : ''}</span>
            <span class="badge badge-${b.status.toLowerCase()}">${b.status}</span>
          </div>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error(err);
  }

  // Load Profile Snapshot
  try {
    const profile = await apiCall('/profile/me');
    const profCard = document.getElementById('guest-profile-card');
    if (profCard && profile) {
      profCard.innerHTML = `
        <h3 style="color:var(--primary-gold); font-size:1.15rem; margin-bottom:14px;">👤 بيانات الملف الشخصي</h3>
        <div style="font-size:0.9rem; line-height:2;">
          <div><strong>الاسم:</strong> ${profile.full_name}</div>
          <div><strong>الهاتف:</strong> ${profile.phone_number}</div>
          <div><strong>المحافظة:</strong> ${profile.governorate}</div>
          <div><strong>الكنيسة:</strong> ${profile.church}</div>
          <div><strong>عدد الخلوات السابقة:</strong> ${profile.total_retreats_count}</div>
          <div><strong>آخر خلوة:</strong> ${profile.last_retreat_date || 'لا يوجد'}</div>
        </div>
      `;
    }
  } catch(e) {}

  // Load Notifications
  loadGuestNotifications();
}

async function loadGuestNotifications() {
  const container = document.getElementById('guest-notifications-list');
  if (!container) return;

  try {
    const notifs = await apiCall('/notifications');
    if (!notifs || notifs.length === 0) {
      container.innerHTML = `<p class="text-muted" style="font-size:0.85rem;">لا توجد إشعارات حالياً.</p>`;
      return;
    }

    container.innerHTML = notifs.map(n => `
      <div style="padding:10px 12px; background:${n.is_read ? 'rgba(15,23,42,0.3)' : 'rgba(212,175,55,0.1)'}; border-radius:8px; margin-bottom:8px; border-right:3px solid ${n.severity==='SUCCESS'?'#10B981':n.severity==='URGENT'?'#F43F5E':'#D4AF37'};">
        <div style="font-size:0.85rem; font-weight:700; color:var(--text-primary); margin-bottom:2px;">${n.title}</div>
        <div style="font-size:0.8rem; color:var(--text-secondary); line-height:1.5;">${n.message}</div>
        <small class="text-muted" style="font-size:0.75rem;">${n.created_at ? n.created_at.slice(0,16).replace('T', ' ') : ''}</small>
      </div>
    `).join('');
  } catch(e) {}
}

async function markAllNotificationsRead() {
  try {
    await apiCall('/notifications/read-all', { method: 'PUT' });
    loadGuestNotifications();
    showToast('تم تحديد جميع الإشعارات كمقروءة', 'success');
  } catch(e) {}
}

function openExtensionModal(bookingId) {
  document.getElementById('ext-booking-id').value = bookingId;
  openModal('extension-modal');
}

async function handleExtensionSubmit(event) {
  event.preventDefault();
  const bookingId = document.getElementById('ext-booking-id').value;
  const days = parseInt(document.getElementById('ext-days').value);
  const reason = document.getElementById('ext-reason').value;
  const details = document.getElementById('ext-details').value;

  try {
    await apiCall(`/bookings/${bookingId}/request-extension`, {
      method: 'POST',
      body: {
        requested_additional_days: days,
        reason: reason,
        detailed_explanation: details
      }
    });

    closeModal('extension-modal');
    showToast('تم إرسال طلب التمديد بنجاح للأم المسؤولة', 'success');
    loadGuestDashboardData();
  } catch(err) {
    showToast(err.message || 'فشل إرسال طلب التمديد', 'danger');
  }
}

async function cancelMyBooking(bookingId) {
  if (!confirm('هل أنتِ متأكدة من الاعتذار عن موعد الخلوة وإلغاء الحجز؟')) return;

  try {
    await apiCall(`/bookings/${bookingId}/cancel`, { method: 'POST' });
    showToast('تم تسجيل الاعتذار وإلغاء الحجز بنجاح', 'info');
    loadGuestDashboardData();
  } catch(err) {
    showToast(err.message || 'فشل إلغاء الحجز', 'danger');
  }
}
