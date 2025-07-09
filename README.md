<div align="center">
    <h1>🏦 حاسبة أذون الخزانة المصرية 🏦</h1>
  <p><strong>تطبيقك الأمثل لتحليل وحساب عوائد أذون الخزانة المصرية بدقة وسهولة.</strong></p>
  
  <p>
    <a href="https://github.com/Al-QaTari/Treasury_Calculator/actions/workflows/quality_check.yml"><img src="https://github.com/Al-QaTari/Treasury_Calculator/actions/workflows/quality_check.yml/badge.svg" alt="Code Quality Check"></a>
    <a href="https://github.com/Al-QaTari/Treasury_Calculator/actions/workflows/scheduled_scrape.yml"><img src="https://github.com/Al-QaTari/Treasury_Calculator/actions/workflows/scheduled_scrape.yml/badge.svg" alt="Scheduled Scrape"></a>
    <a href="https://streamlit.io" target="_blank"><img src="https://img.shields.io/badge/Made_with-Streamlit-FF4B4B?logo=streamlit" alt="Made with Streamlit"></a>
    <a href="https://www.python.org/" target="_blank"><img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python" alt="Python Version"></a>
  </p>
</div>

---

## 📖 جدول المحتويات
1. [عن المشروع](#-عن-المشروع)
2. [الميزات الرئيسية](#-الميزات-الرئيسية)
3. [التشغيل محلياً](#-التشغيل-محلياً)
4. [هيكل المشروع](#-هيكل-المشروع)
5. [الترخيص](#-الترخيص-license)
6. [المساهمة](#-المساهمة)
7. [المؤلف](#-المؤلف)

---

## 🎯 عن المشروع

تطبيق ويب تفاعلي ومفتوح المصدر، تم بناؤه باستخدام **Streamlit** لمساعدة المستثمرين في السوق المصري على اتخاذ قرارات استثمارية مدروسة. يقوم التطبيق بسحب أحدث بيانات عطاءات أذون الخزانة بشكل آلي من موقع البنك المركزي المصري ويحولها إلى أرقام ورؤى واضحة.

---

## ✨ الميزات الرئيسية

| الميزة | الوصف |
| :--- | :--- |
| **📊 جلب آلي للبيانات** | سحب أحدث بيانات العطاءات مباشرة من موقع البنك المركزي المصري لضمان دقة الأرقام. |
| **🧮 حاسبة العائد الأساسية** | حساب صافي الربح، الضرائب، ونسبة العائد الفعلية عند الشراء والاحتفاظ حتى الاستحقاق. |
| **⚖️ حاسبة البيع الثانوي** | تحليل قرار البيع المبكر وحساب الربح أو الخسارة المحتملة بناءً على العائد السائد في السوق. |
| **🗄️ قاعدة بيانات تاريخية** | حفظ البيانات المجلوبة في قاعدة بيانات SQLite لتتبع التغيرات في العوائد مع مرور الوقت. |
| **⚙️ أتمتة كاملة (CI/CD)** | استخدام GitHub Actions لفحص جودة الكود، وتطبيق التنسيق، وتشغيل الاختبارات تلقائياً. |
| **💡 شرح مفصل** | قسم للمساعدة يشرح المفاهيم المالية الأساسية وكيفية عمل الحاسبات. |

---

## 🚀 التشغيل محلياً

اتبع هذه الخطوات لتشغيل المشروع على جهازك.

#### 1️⃣ المتطلبات الأساسية
- Python 3.8 أو أحدث.
- متصفح Google Chrome.
- أداة `git`.

#### 2️⃣ تثبيت المشروع
```bash
# انسخ المستودع إلى جهازك
git clone [https://github.com/Al-QaTari/Treasury_Calculator.git](https://github.com/Al-QaTari/Treasury_Calculator.git)

# ادخل إلى مجلد المشروع
cd Treasury_Calculator

# ثبّت جميع المكتبات المطلوبة
pip install -r requirements.txt
```

#### 3️⃣ تحديث البيانات (خطوة هامة)
```bash
# شغّل سكربت تحديث البيانات لجلب أحدث العوائد
python update_data.py
```
> **ملاحظة:** قد تستغرق هذه العملية دقيقة أو اثنتين في المرة الأولى.

#### 4️⃣ تشغيل التطبيق
```bash
# شغّل تطبيق Streamlit
streamlit run app.py
```
سيفتح التطبيق تلقائيًا في متصفحك على `http://localhost:8501`.

---

## 📂 هيكل المشروع
```
Treasury_Calculator/
│
├── .github/
│   └── workflows/
│       ├── quality_check.yml     # ملف فحص الجودة والتنسيق الآلي (CI)
│       └── scheduled_scrape.yml  # ملف جدولة جلب البيانات الآلي
│
├── css/
│   └── style.css                 # ملف التنسيقات (CSS) لواجهة المستخدم
│
├── tests/
│   ├── test_calculations.py      # اختبارات الدوال الحسابية
│   ├── test_cbe_scraper.py       # (جديد) اختبارات تحليل HTML الوهمي
│   └── test_db_manager.py        # (جديد) اختبارات مدير قاعدة البيانات
│
├── app.py                        # التطبيق الرئيسي وواجهة المستخدم (Streamlit)
├── calculations.py               # الدوال الخاصة بالعمليات الحسابية المالية
├── cbe_scraper.py                # منطق جلب البيانات من موقع البنك المركزي
├── constants.py                  # جميع الثوابت والمتغيرات المركزية
├── db_manager.py                 # كلاس لإدارة قاعدة البيانات (SQLite)
├── update_data.py                # سكربت لتشغيل عملية تحديث البيانات يدوياً
├── utils.py                      # دوال مساعدة (مثل معالجة النصوص والتنسيق)
│
├── .gitignore                    # لتجاهل الملفات غير المرغوب فيها
├── LICENSE.txt                   # ملف الترخيص (MIT)
├── README.md                     # ملف التوثيق هذا
├── packages.txt                  # (جديد) ملف الحزم المطلوبة لسيرفر Streamlit
└── requirements.txt              # قائمة المكتبات المطلوبة لتشغيل المشروع

---

## 📜 الترخيص (License)

هذا المشروع مرخص بموجب **ترخيص MIT**، وهو أحد أكثر تراخيص البرمجيات الحرة تساهلاً. هذا يمنحك حرية كبيرة في استخدام وتطوير البرنامج.

#### ✓ لك مطلق الحرية في:
- **الاستخدام التجاري**: يمكنك استخدام هذا البرنامج في أي مشروع تجاري وتحقيق الربح منه.
- **التعديل والتطوير**: يمكنك تعديل الكود المصدري ليناسب احتياجاتك الخاصة.
- **التوزيع**: يمكنك إعادة توزيع البرنامج بنسخته الأصلية أو بعد تعديله.

#### ⚠️ الشرط الوحيد:
- **الإبقاء على الإشعار**: يجب عليك الإبقاء على إشعار حقوق النشر والترخيص الأصلي مضمنًا في جميع نسخ البرنامج.

#### 🚫 إخلاء المسؤولية:
- **بدون ضمان**: البرنامج مقدم "كما هو" دون أي ضمان من أي نوع، سواء كان صريحًا أو ضمنيًا.
- **بدون مسؤولية**: لا يتحمل المؤلفون أي مسؤولية عن أي أضرار قد تنشأ عن استخدام البرنامج.

<p align="center">
  <a href="https://github.com/Al-QaTari/Treasury_Calculator/blob/main/LICENSE.txt">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
  </a>
  <br>
  <small>للاطلاع على النص الكامل للترخيص، اضغط على الشارة أعلاه</small>
</p>

---

## 🤝 المساهمة

المساهمات هي ما تجعل مجتمع المصادر المفتوحة مكانًا رائعًا للتعلم والإلهام والإبداع. أي مساهمات تقدمها ستكون موضع **تقدير كبير**.

1.  قم بعمل Fork للمشروع.
2.  أنشئ فرعًا جديدًا للميزة الخاصة بك (`git checkout -b feature/AmazingFeature`).
3.  قم بعمل Commit لتغييراتك (`git commit -m 'Add some AmazingFeature'`).
4.  ارفع تغييراتك إلى الفرع (`git push origin feature/AmazingFeature`).
5.  افتح Pull Request.

---

## ✍️ المؤلف

**Mohamed AL-QaTri** - [GitHub](https://github.com/Al-QaTari)

---

### إخلاء مسؤولية
هذا التطبيق هو أداة إرشادية فقط. للحصول على أرقام نهائية ودقيقة، يرجى الرجوع دائمًا إلى البنك أو المؤسسة المالية التي تتعامل معها.
