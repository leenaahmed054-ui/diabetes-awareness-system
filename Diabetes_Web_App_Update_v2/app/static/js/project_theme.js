(() => {
  const root = document.documentElement;
  const toggle = document.getElementById('languageToggle');
  const splash = document.getElementById('splash');
  const digitMap = {'٠':'0','١':'1','٢':'2','٣':'3','٤':'4','٥':'5','٦':'6','٧':'7','٨':'8','٩':'9','۰':'0','۱':'1','۲':'2','۳':'3','۴':'4','۵':'5','۶':'6','۷':'7','۸':'8','۹':'9'};
  const normalizeDigits = value => String(value).replace(/[٠-٩۰-۹]/g, d => digitMap[d]);

  function applyLanguage(language) {
    const arabic = language === 'ar';
    root.lang = language;
    root.dir = arabic ? 'rtl' : 'ltr';
    root.dataset.language = language;
    localStorage.setItem('projectLanguage', language);
    document.querySelectorAll('[data-en][data-ar]').forEach(node => {
      node.textContent = node.dataset[language];
    });
    document.querySelectorAll('[data-placeholder-en][data-placeholder-ar]').forEach(node => {
      node.placeholder = node.dataset[arabic ? 'placeholderAr' : 'placeholderEn'];
    });
    if (toggle) toggle.textContent = arabic ? 'English' : 'العربية';
    document.querySelectorAll('input[type=number]').forEach(input => input.lang = 'en-US');
    const optionText = {
      gender: {male:['Male','ذكر'], female:['Female','أنثى']},
      physically_active: {'1':['Yes','نعم'], '0':['No','لا']},
      pregnancy_status: {
        not_applicable:['Not applicable','لا ينطبق'],
        not_pregnant:['Not pregnant','غير حامل'],
        pregnant:['Pregnant','حامل'],
        not_collected:['Prefer not to say','أفضل عدم الإفصاح']
      }
    };
    Object.entries(optionText).forEach(([id, options]) => {
      const select = document.getElementById(id);
      if (!select) return;
      [...select.options].forEach(option => {
        if (options[option.value]) option.textContent = options[option.value][arabic ? 1 : 0];
      });
    });
    const awarenessAr = {
      bmi: {Underweight:'مؤشر كتلة الجسم أقل من النطاق الصحي العام للبالغين. يُنصح بمناقشة التغذية وتغيرات الوزن مع مختص صحي مؤهل.','Healthy range':'مؤشر كتلة الجسم ضمن النطاق الصحي العام للبالغين. حافظ على تغذية متوازنة ونشاط بدني منتظم.',Overweight:'مؤشر كتلة الجسم ضمن نطاق زيادة الوزن. قد تساعد التحسينات التدريجية في التغذية والنشاط على تقليل المخاطر الصحية.','Obesity range':'مؤشر كتلة الجسم ضمن نطاق السمنة. ناقش أهدافًا صحية آمنة وواقعية مع مختص صحي مؤهل.'},
      physical_activity:'يساعد النشاط البدني المنتظم في دعم الصحة وتقليل خطر السكري. اختر نوعًا وشدة مناسبين لحالتك الصحية وابدأ تدريجيًا عند الحاجة.',
      blood_pressure:'تم تحليل قراءة ضغط الدم للتوعية العامة. القراءة الواحدة لا تكفي للتشخيص؛ كرر القياس بصورة صحيحة وناقش القراءات المرتفعة أو الأعراض مع مختص صحي.',
      glucose:'يجب تفسير الجلوكوز حسب نوع القياس: صائم أو عشوائي أو فحص رسمي. التطبيق لا يسجل هذا السياق، لذلك لا يمكن اعتبار القيمة تشخيصًا للسكري.',
      pregnancy:'الحمل يحتاج تقييمًا طبيًا خاصًا. النموذج العام في هذا الموقع لا يشخّص سكري الحمل، لذا اتبعي جدول الفحوص الذي يوصي به الطبيب.',
      pregnancy_screening:'النتيجة أعلاه من نموذج عام للبالغين ولا تشخّص سكري الحمل. يُجرى الفحص غالبًا بين الأسبوعين 24 و28، أو أبكر إذا رأى فريق متابعة الحمل وجود خطورة أعلى. التزمي بمواعيد متابعة الحمل وخطة الفحص التي يحددها الفريق الطبي.',
      pregnancy_pressure:'ضغط الدم أثناء الحمل يحتاج تفسيرًا خاصًا. ناقشي سريعًا مع فريق الحمل أي قراءة متكررة 140/90 أو أعلى. اطلبي رعاية عاجلة عند القراءة الشديدة أو الصداع المستمر أو تغير الرؤية أو ألم أعلى البطن أو صعوبة التنفس أو التورم المفاجئ.',
      pregnancy_lifestyle:'لا تبدئي برنامجًا لتقليل الوزن أثناء الحمل. اتبعي إرشادات فريق الحمل بشأن زيادة الوزن الصحية والغذاء المتوازن والسوائل والنشاط. عند عدم وجود مانع طبي، قد يدعم النشاط المعتدل المنتظم صحة الأم.',
      pregnancy_ramadan:'الحمل والصيام يحتاجان تقييمًا طبيًا فرديًا. ناقشي الصيام مع طبيبة النساء أو المختص قبل رمضان، خصوصًا عند وجود قراءات غير معتادة للسكر أو ضغط الدم.'
    };
    document.querySelectorAll('[data-awareness]').forEach(card => {
      const message = card.querySelector('.awareness-message');
      if (!message) return;
      if (!message.dataset.en) message.dataset.en = message.textContent.trim();
      let arabic = awarenessAr[card.dataset.awareness];
      if (card.dataset.awareness === 'bmi') arabic = awarenessAr.bmi[card.dataset.bmiCategory];
      if (card.dataset.awareness === 'pregnancy' && card.dataset.pregnancyStatus !== 'pregnant') arabic = 'معلومات الحمل محفوظة بصورة منفصلة عن نموذج التنبؤ العام وتستخدم للتوعية فقط.';
      message.textContent = arabic && root.lang === 'ar' ? arabic : message.dataset.en;
    });
  }

  applyLanguage(localStorage.getItem('projectLanguage') || 'en');
  toggle?.addEventListener('click', () => applyLanguage(root.lang === 'ar' ? 'en' : 'ar'));
  document.querySelectorAll('form').forEach(form => form.addEventListener('submit', () => {
    form.querySelectorAll('input').forEach(input => {
      if (input.type !== 'password') input.value = normalizeDigits(input.value);
    });
  }));

  if (splash) {
    const firstVisit = !sessionStorage.getItem('projectSplashSeen');
    setTimeout(() => splash.classList.add('hidden'), firstVisit ? 2000 : 0);
    sessionStorage.setItem('projectSplashSeen', '1');
  }

  const gender = document.getElementById('gender');
  const pregnancy = document.getElementById('pregnancyFields');
  function updatePregnancy() {
    if (!gender || !pregnancy) return;
    const female = gender.value === 'female';
    pregnancy.hidden = !female;
    pregnancy.querySelectorAll('select,input').forEach(field => field.disabled = !female);
    const status = document.getElementById('pregnancy_status');

    if (status) {
      status.hidden = !female;

      if (!female) {
        status.disabled = false;
        status.value = 'not_applicable';
      }
    }
  }
  gender?.addEventListener('change', updatePregnancy);
  updatePregnancy();
})();
