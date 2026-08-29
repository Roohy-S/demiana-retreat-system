/**
 * Landing Page & Spiritual House Regulations View
 */

async function renderLandingView(container) {
  container.innerHTML = `
    <!-- Hero Section -->
    <div class="hero-section">
      <img src="/static/images/cross.png" alt="الصليب القبطي" class="hero-cross-centered" />
      <h1 class="hero-title">بيت الخلوة بدير القديسة دميانة</h1>
      <p class="hero-location">ببراري بلقاس – محافظة الدقهلية</p>
      
      <!-- Scripture Verse -->
      <div class="verse-banner">
        <div class="verse-text">«أَمَّا هُوَ فَكَانَ يَعْتَزِلُ فِي الْبَرَارِي وَيُصَلِّي»</div>
        <div class="verse-ref">(إنجيل لوقا 5 : 16)</div>
      </div>

      <div style="display:flex; justify-content:center; gap:16px; margin-top:20px;">
        <button class="btn btn-lg btn-primary" onclick="navigate('register_wizard')">
          <span>✝</span> تقديم طلب حجز خلوة
        </button>
        <button class="btn btn-lg btn-secondary" onclick="document.getElementById('bylaws-section').scrollIntoView({behavior:'smooth'})">
          لائحة وتعليمات البيت
        </button>
      </div>
    </div>

    <!-- Available Periods Section -->
    <div class="container" style="margin-bottom: 50px;">
      <div class="section-header">
        <div class="section-title">
          <span>📅</span> فترات الخلوة المتاحة للحجز
        </div>
        <span class="text-muted" style="font-size:0.9rem;">المدة الافتراضية: 3 ليالٍ (المغادرة اليوم الرابع قبل 9:00 ص)</span>
      </div>

      <div id="periods-list-container" class="grid grid-cols-3">
        <div style="grid-column: 1/-1; text-align:center; padding:30px;" class="glass-card">
          <p>جاري تحميل الفترات المتاحة...</p>
        </div>
      </div>
    </div>

    <!-- Bylaws & Regulations Section -->
    <div id="bylaws-section" class="container" style="margin-bottom: 60px;">
      <div class="section-header">
        <div class="section-title">
          <span>📜</span> لائحة ونظام بيت الخلوة بدير القديسة دميانة
        </div>
        <span class="badge badge-under_review">مُلزمة لجميع النزيلات</span>
      </div>

      <!-- Regulations Tabs -->
      <div class="tabs-nav" id="bylaws-tabs">
        <button class="tab-btn active" onclick="switchBylawTab('prayers')">مواعيد الصلوات</button>
        <button class="tab-btn" onclick="switchBylawTab('meals')">مواعيد المائدة</button>
        <button class="tab-btn" onclick="switchBylawTab('canteen')">الكانتين والزيارة</button>
        <button class="tab-btn" onclick="switchBylawTab('silence')">إطفاء الأنوار والصمت</button>
        <button class="tab-btn" onclick="switchBylawTab('rule')">قانون الصلاة</button>
        <button class="tab-btn" onclick="switchBylawTab('general')">التعليمات العامة وتنبيهات الحجز</button>
      </div>

      <!-- Bylaws Content Cards -->
      <div id="bylaw-content-area" class="glass-card gold-glow">
        <!-- Injected via switchBylawTab -->
      </div>
    </div>

    <!-- Daily Program Timeline Section -->
    <div class="container" style="margin-bottom: 80px;">
      <div class="section-header">
        <div class="section-title">
          <span>⏱</span> البرنامج والجدول اليومي الإلزامي
        </div>
        <span class="text-gold" style="font-weight:600;">الانضباط والهدوء سر الاستفادة الروحية</span>
      </div>

      <div class="timeline-container">
        <div class="timeline-item">
          <div class="timeline-icon-box">🕯</div>
          <div class="timeline-content-card">
            <span class="timeline-time">5:00 ص – 9:00 ص</span>
            <div class="timeline-title">القداس الإلهي / خلوة فردية</div>
            <p class="text-muted">حضور القداس الإلهي بكنائس الدير أو ممارسة خلوة فردية هادئة بالقلاية.</p>
          </div>
        </div>

        <div class="timeline-item">
          <div class="timeline-icon-box">🍞</div>
          <div class="timeline-content-card">
            <span class="timeline-time">9:00 ص – 9:30 ص</span>
            <div class="timeline-title">وجبة الإفطار</div>
            <p class="text-muted">بالمائدة (باستثناء أيام الصوم الانقطاعي والأربعاء والجمعة).</p>
          </div>
        </div>

        <div class="timeline-item">
          <div class="timeline-icon-box">📖</div>
          <div class="timeline-content-card">
            <span class="timeline-time">9:30 ص – 11:00 ص</span>
            <div class="timeline-title">فترة خلوة صباحية</div>
            <p class="text-muted">قراءة روحية، دراسة الكتاب المقدس، والتأمل الهادئ.</p>
          </div>
        </div>

        <div class="timeline-item">
          <div class="timeline-icon-box">🧹</div>
          <div class="timeline-content-card">
            <span class="timeline-time">11:00 ص – 12:00 ظهراً</span>
            <div class="timeline-title">فترة عمل ونظافة</div>
            <p class="text-muted">نظافة بيت الخلوة والقلالي وترتيب الأماكن.</p>
          </div>
        </div>

        <div class="timeline-item">
          <div class="timeline-icon-box">🎬</div>
          <div class="timeline-content-card">
            <span class="timeline-time">12:00 ظهراً – 1:30 ظهراً</span>
            <div class="timeline-title">فيلم روحي اختياري</div>
            <p class="text-muted">عرض أفلام روحية ووثائقية عن سير القديسين وتاريخ الكنيسة.</p>
          </div>
        </div>

        <div class="timeline-item">
          <div class="timeline-icon-box">🍲</div>
          <div class="timeline-content-card">
            <span class="timeline-time">2:00 ظهراً – 2:30 ظهراً</span>
            <div class="timeline-title">وجبة الغداء</div>
            <p class="text-muted">بالمائدة طوال أيام الأسبوع ما عدا السبت والأحد.</p>
          </div>
        </div>

        <div class="timeline-item">
          <div class="timeline-icon-box">⛪</div>
          <div class="timeline-content-card">
            <span class="timeline-time">2:30 م – 4:00 م</span>
            <div class="timeline-title">زيارة كنيسة القبر وكنائس الدير + تمجيد</div>
            <p class="text-muted">النزول لكنيسة القبر للتبرك وعمل تمجيد للقديسة دميانة والأربعين عذراء وخلوة فردية.</p>
          </div>
        </div>

        <div class="timeline-item">
          <div class="timeline-icon-box">🔔</div>
          <div class="timeline-content-card">
            <span class="timeline-time">4:30 م – 5:00 م</span>
            <div class="timeline-title">صلوات المجمع</div>
            <p class="text-muted">الاشتراك في صلوات المجمع (ممنوع التواجد خارج بيت الخلوة بعد 4:30 م نهائياً).</p>
          </div>
        </div>

        <div class="timeline-item">
          <div class="timeline-icon-box">📚</div>
          <div class="timeline-content-card">
            <span class="timeline-time">5:00 م – 6:00 م</span>
            <div class="timeline-title">مكتبة الاستعارة</div>
            <p class="text-muted">استعارة كتب روحية وإرشادية من مكتبة بيت الخلوة.</p>
          </div>
        </div>

        <div class="timeline-item">
          <div class="timeline-icon-box">🕯</div>
          <div class="timeline-content-card">
            <span class="timeline-time">6:00 م – 7:30 م</span>
            <div class="timeline-title">خلوة فردية مسائية</div>
            <p class="text-muted">وقت خاص مع النفس والله داخل القلاية.</p>
          </div>
        </div>

        <div class="timeline-item">
          <div class="timeline-icon-box">🥗</div>
          <div class="timeline-content-card">
            <span class="timeline-time">7:30 م – 8:00 م</span>
            <div class="timeline-title">وجبة العشاء</div>
            <p class="text-muted">تناول طعام العشاء بالمائدة بهدوء ونظام.</p>
          </div>
        </div>

        <div class="timeline-item">
          <div class="timeline-icon-box">🎶</div>
          <div class="timeline-content-card">
            <span class="timeline-time">8:30 م – 11:00 م</span>
            <div class="timeline-title">تسبحة نصف الليل</div>
            <p class="text-muted">صلاة التسبحة كل الأيام، ويتم التنبيه عن موعد القداس بعدها.</p>
          </div>
        </div>

        <div class="timeline-item">
          <div class="timeline-icon-box">🌙</div>
          <div class="timeline-content-card" style="border-color: rgba(212, 175, 55, 0.4);">
            <span class="timeline-time">11:00 م – 6:00 ص</span>
            <div class="timeline-title">فترة الصمت وإطفاء الأنوار</div>
            <p class="text-muted">إطفاء الأنوار بالقلالي، التزام الصمت التام، وغلق القلالي بالمفتاح.</p>
          </div>
        </div>
      </div>
    </div>
  `;

  loadLandingPeriods();
  switchBylawTab('prayers');
}

// Load Periods dynamically
async function loadLandingPeriods() {
  const container = document.getElementById('periods-list-container');
  if (!container) return;

  try {
    const periods = await apiCall('/periods');
    if (!periods || periods.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1/-1; text-align:center; padding:30px;" class="glass-card">
          <p class="text-gold">لا توجد فترات مفتوحة للحجز حالياً. يتم فتح الفترات دورياً من إدارة الدير.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = periods.map(p => {
      const isFull = p.status === 'FULL' || p.remaining_spots <= 0;
      const nightsCount = p.nights_count || 3;
      const totalDays = nightsCount + 1;
      return `
        <div class="glass-card ${isFull ? '' : 'gold-glow'}" style="display:flex; flex-direction:column; justify-content:space-between;">
          <div>
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px; gap:8px;">
              <h3 style="font-size:1.15rem; color:var(--text-primary);">${p.period_name}</h3>
              <span class="badge ${isFull ? 'badge-waiting_list' : 'badge-approved'}">
                ${isFull ? 'مكتملة (انتظار)' : 'متاحة للحجز'}
              </span>
            </div>

            <div style="font-size:0.9rem; color:var(--text-secondary); margin-bottom:18px; line-height:1.8;">
              <div>📅 <strong>الوصول (البداية):</strong> ${formatArabicDate(p.start_date)}</div>
              <div>🚪 <strong>المغادرة (النهاية):</strong> ${formatArabicDate(p.departure_date)} <span class="text-muted">(${p.departure_time_desc || 'قبل 9:00 ص'})</span></div>
              <div>🌙 <strong>المدة:</strong> <span style="color:var(--primary-gold); font-weight:700;">${nightsCount} ليالي (${totalDays} أيام)</span></div>
              <div>🛏️ <strong>السعة الكلية:</strong> ${p.capacity} مكان 
                <span style="color:var(--primary-gold); font-weight:800; margin-right:4px;">(متبقي: ${p.remaining_spots} سرير)</span>
              </div>
            </div>
          </div>

          <button class="btn btn-primary" style="width:100%;" onclick="navigate('register_wizard', { selectedPeriodId: '${p.id}' })">
            ${isFull ? 'طلب الانضمام لقائمة الانتظار' : '✝ احجزي في هذه الفترة'}
          </button>
        </div>
      `;
    }).join('');

  } catch (err) {
    container.innerHTML = `<div style="grid-column:1/-1; text-align:center; color:#F43F5E;">تعذر تحميل فترات الخلوة.</div>`;
  }
}

// Bylaws Tabs Switcher
function switchBylawTab(tabKey) {
  const tabsNav = document.getElementById('bylaws-tabs');
  if (tabsNav) {
    Array.from(tabsNav.children).forEach(btn => btn.classList.remove('active'));
    event && event.target && event.target.classList.add('active');
  }

  const contentArea = document.getElementById('bylaw-content-area');
  if (!contentArea) return;

  if (tabKey === 'prayers') {
    contentArea.innerHTML = `
      <h3 style="color:var(--primary-gold); margin-bottom:15px;">أولاً: المواعيد المُلزمة لبيت الخلوة - الصلوات</h3>
      <ul style="list-style-type: none; line-height:2.2; font-size:1.05rem;">
        <li>🔹 <strong>صلوات المجمع:</strong> الساعة 4:30 مساءً يومياً.</li>
        <li>🔹 <strong>تسبحة نصف الليل:</strong> كل الأيام الساعة 8:30 مساءً.</li>
        <li>🔹 <strong>القداس الإلهي:</strong> يتم التنبيه عن موعده في نفس اليوم بعد صلاة التسبحة.</li>
      </ul>
    `;
  } else if (tabKey === 'meals') {
    contentArea.innerHTML = `
      <h3 style="color:var(--primary-gold); margin-bottom:15px;">ثانياً: مواعيد المائدة</h3>
      <div class="grid grid-cols-3" style="gap:15px; margin-top:15px;">
        <div style="background:rgba(15,23,42,0.6); padding:16px; border-radius:10px; border:1px solid var(--border-subtle);">
          <div style="color:var(--primary-gold); font-weight:700; margin-bottom:6px;">🍳 الإفطار</div>
          <div>من <strong>9:00 ص</strong> إلى <strong>9:30 ص</strong></div>
          <small class="text-muted">(باستثناء أيام الصوم الانقطاعي والأربعاء والجمعة)</small>
        </div>

        <div style="background:rgba(15,23,42,0.6); padding:16px; border-radius:10px; border:1px solid var(--border-subtle);">
          <div style="color:var(--primary-gold); font-weight:700; margin-bottom:6px;">🍲 الغداء</div>
          <div>من <strong>2:00 ظ</strong> إلى <strong>2:30 ظ</strong></div>
          <small class="text-muted">(طوال أيام الأسبوع ما عدا السبت والأحد)</small>
        </div>

        <div style="background:rgba(15,23,42,0.6); padding:16px; border-radius:10px; border:1px solid var(--border-subtle);">
          <div style="color:var(--primary-gold); font-weight:700; margin-bottom:6px;">🥗 العشاء</div>
          <div>من <strong>7:30 م</strong> إلى <strong>8:00 م</strong></div>
          <small class="text-muted">(يومياً لجميع النزيلات)</small>
        </div>
      </div>
    `;
  } else if (tabKey === 'canteen') {
    contentArea.innerHTML = `
      <h3 style="color:var(--primary-gold); margin-bottom:15px;">ثالثاً: الكانتين والنزول لكنيسة القبر</h3>
      <div class="grid grid-cols-2" style="gap:20px;">
        <div style="background:rgba(15,23,42,0.6); padding:18px; border-radius:10px;">
          <h4 style="color:var(--primary-gold); margin-bottom:10px;">🛒 فترات فتح الكانتين:</h4>
          <ul style="list-style:none; line-height:2;">
            <li>🔸 <strong>الفترة الأولى:</strong> 9:00 صباحاً ➔ 4:00 مساءً</li>
            <li>🔸 <strong>الفترة الثانية:</strong> 7:00 مساءً ➔ 8:00 مساءً</li>
            <li>🔸 <strong>الفترة الثالثة:</strong> 9:00 مساءً ➔ 10:00 مساءً</li>
          </ul>
          <p class="text-gold" style="margin-top:10px; font-size:0.9rem;">(ملحوظة: يوجد مشروبات دافئة وباردة بالكانتين)</p>
        </div>

        <div style="background:rgba(15,23,42,0.6); padding:18px; border-radius:10px;">
          <h4 style="color:var(--primary-gold); margin-bottom:10px;">⛪ النزول لكنيسة القبر:</h4>
          <p style="line-height:1.9;">
            النزول لكنيسة القبر بعد الغداء من <strong>2:30 ظ إلى 4:00 م</strong> لعمل:
            <br>• تمجيد للقديسة دميانة والأربعين عذراء.
            <br>• خلوة فردية هادئة والتبرك.
          </p>
        </div>
      </div>
    `;
  } else if (tabKey === 'silence') {
    contentArea.innerHTML = `
      <h3 style="color:var(--primary-gold); margin-bottom:15px;">رابعاً: إطفاء الأنوار والصمت</h3>
      <div style="background:rgba(15,23,42,0.7); padding:20px; border-radius:12px; border-right:4px solid var(--primary-gold);">
        <p style="font-size:1.15rem; line-height:2;">
          🌙 <strong>إطفاء الأنوار في القلالي والتزام الصمت التام:</strong> يبدأ من الساعة <strong>11:00 مساءً</strong> حتى <strong>6:00 صباحاً</strong>.
          <br>🔐 يُرجى غلق القلاية بالمفتاح عند عدم تواجد أحد بها (أثناء التسبحة، المجمع، القداس، أو زيارة الدير).
        </p>
      </div>
    `;
  } else if (tabKey === 'rule') {
    contentArea.innerHTML = `
      <h3 style="color:var(--primary-gold); margin-bottom:15px;">خامساً: قانون الصلاة المتبع في بيت الخلوة</h3>
      <div class="grid grid-cols-2" style="gap:20px;">
        <div style="background:rgba(15,23,42,0.6); padding:18px; border-radius:10px; border:1px solid var(--border-light);">
          <h4 style="color:var(--primary-gold); margin-bottom:10px;">القانون المتبع الأساسي:</h4>
          <ul style="list-style:none; line-height:2.2;">
            <li>🙏 <strong>1000 مرة</strong> صلاة يسوع في اليوم («يا ربي يسوع المسيح ارحمني أنا الخاطئ»).</li>
            <li>📖 <strong>50 مزمور</strong> في اليوم واستخراج صلوات يسوع وتأملات منها.</li>
            <li>✍️ الالتزام بحل واجب بيت الخلوة الروحي.</li>
          </ul>
        </div>

        <div style="background:rgba(15,23,42,0.6); padding:18px; border-radius:10px; border:1px solid var(--border-subtle);">
          <h4 style="color:var(--primary-gold); margin-bottom:10px;">في حالة عدم وجود قانون صلاة محدد:</h4>
          <ul style="list-style:none; line-height:2.2;">
            <li>📖 <strong>الصلاة بالأجبية:</strong> باكر، غروب، ونوم (في كل صلاة 3 مزامير فأكثر).</li>
            <li>📜 <strong>قراءة الكتاب المقدس:</strong> إصحاحين عهد قديم + 3 إصحاحات عهد جديد فأكثر (أو حسب قانونكِ مع أب الاعتراف).</li>
          </ul>
        </div>
      </div>
    `;
  } else if (tabKey === 'general') {
    contentArea.innerHTML = `
      <h3 style="color:var(--primary-gold); margin-bottom:15px;">سادساً: التعليمات العامة وتنبيهات الحجز</h3>
      <div style="display:grid; grid-template-columns:1fr; gap:12px; line-height:1.9;">
        <div style="background:rgba(15,23,42,0.5); padding:12px 18px; border-radius:8px;">
          📱 <strong>تسليم الموبايل:</strong> يتم تسليم الموبايل عند الحضور، ويوجد موبايل ببيت الخلوة للطوارئ. يُرجى تدوين الأرقام المهمة خارجياً لعدم طلب الموبايل نهائياً أثناء الخلوة.
        </div>
        <div style="background:rgba(15,23,42,0.5); padding:12px 18px; border-radius:8px;">
          👗 <strong>الملابس والوقار:</strong> اللبس محتشم ولائق ببيت الخلوة والدير والكنيسة، وارتداء الإشارب أثناء الصلوات.
        </div>
        <div style="background:rgba(15,23,42,0.5); padding:12px 18px; border-radius:8px;">
          ✝️ <strong>المستلزمات الشخصية:</strong> إحضار البطاقة الشخصية، الكتاب المقدس الخاص، الأجبية، وجواب موافقة أب الاعتراف.
        </div>
        <div style="background:rgba(15,23,42,0.5); padding:12px 18px; border-radius:8px;">
          🕊 <strong>مجانية الخلوة:</strong> الخلوة وجميع الوجبات مجانية بالكامل. البيت مفتوح طوال العام ما عدا صوم الميلاد والصوم الكبير وشهر 5 (احتفالات عيد القديسة دميانة).
        </div>
        <div style="background:rgba(15,23,42,0.5); padding:12px 18px; border-radius:8px;">
          🚫 <strong>مواعيد التواجد بالدير:</strong> ممنوع التواجد خارج بيت الخلوة بعد الساعة 4:30 م نهائياً وعدم الاستئذان بذلك لأي سبب.
        </div>
      </div>
    `;
  }
}

// Login View Renderer
function renderLoginView(container) {
  container.innerHTML = `
    <div class="container" style="max-width:500px; padding-top:45px; padding-bottom:70px;">
      <div class="glass-card gold-glow animate-scale-in" style="padding:32px 28px;">
        <div style="text-align:center; margin-bottom:20px;">
          <img src="/static/images/cross.png" style="height:64px; margin-bottom:12px;" />
          <h2 style="color:var(--primary-gold); font-size:1.6rem; margin-bottom:4px;">دخول نظام بيت الخلوة</h2>
          <p class="text-muted" style="font-size:0.88rem;">دير القديسة دميانة العامر ببراري بلقاس</p>
        </div>

        <div class="auth-nav-tabs">
          <button class="auth-nav-tab active">تسجيل الدخول</button>
          <button class="auth-nav-tab" onclick="navigate('register_wizard')">إنشاء حساب / طلب خلوة</button>
        </div>

        <form id="login-form" onsubmit="handleLoginSubmit(event)">
          <div class="form-group">
            <label class="form-label required">البريد الإلكتروني أو رقم الهاتف أو الرقم القومي</label>
            <input type="text" id="login-identifier" class="form-control" required placeholder="example@gmail.com أو 01012345678 أو الرقم القومي" dir="auto" />
            <span class="text-muted" style="font-size:0.75rem;">يمكنكِ الدخول بالبريد الإلكتروني، أو رقم الموبايل المسجل، أو الرقم القومي (14 رقماً).</span>
          </div>

          <div class="form-group">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
              <label class="form-label required" style="margin-bottom:0;">كلمة المرور</label>
              <a href="javascript:void(0)" onclick="openForgotPasswordModal()" class="auth-link" style="font-size:0.82rem;">
                نسيت كلمة المرور؟
              </a>
            </div>
            <div class="password-input-wrapper">
              <input type="password" id="login-password" class="form-control" required placeholder="••••••••" />
              <button type="button" class="btn-toggle-password" onclick="togglePasswordVisibility('login-password', this)" title="إظهار/إخفاء كلمة المرور">
                👁️
              </button>
            </div>
          </div>

          <button type="submit" id="login-submit-btn" class="btn btn-primary btn-block" style="margin-top:16px; font-size:1.05rem; padding:12px;">
            دخول النظام ➔
          </button>
        </form>

        <div style="text-align:center; margin-top:24px; padding-top:18px; border-top:1px solid var(--border-subtle); font-size:0.9rem;">
          <span class="text-muted">مستخدمة جديدة؟ ليس لديكِ حساب؟</span><br>
          <a href="javascript:void(0)" onclick="navigate('register_wizard')" class="auth-link" style="display:inline-block; margin-top:6px;">
            + إنشاء حساب وتقديم طلب خلوة جديد
          </a>
        </div>
      </div>
    </div>
  `;
}

async function handleLoginSubmit(event) {
  event.preventDefault();
  const identifier = document.getElementById('login-identifier').value.trim();
  const password = document.getElementById('login-password').value;
  const submitBtn = document.getElementById('login-submit-btn');

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerText = 'جاري التحقق والدخول...';
  }

  try {
    const res = await apiCall('/auth/login', {
      method: 'POST',
      body: { identifier, password }
    });

    setAuth(res.access_token, {
      id: res.user_id,
      email: res.email,
      role: res.role
    });

    showToast('تم تسجيل الدخول بنجاح', 'success');

    if (res.role !== 'APPLICANT') {
      navigate('admin_dashboard');
    } else {
      navigate('guest_dashboard');
    }
  } catch (err) {
    showToast(err.message || 'فشل تسجيل الدخول', 'danger');
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerText = 'دخول النظام ➔';
    }
  }
}


