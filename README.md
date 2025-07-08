# 🏦 حاسبة أذون الخزانة المصرية

[![Python Code Quality Check](https://github.com/Al-QaTari/Treasury_Calculator/actions/workflows/quality_check.yml/badge.svg)](https://github.com/Al-QaTari/Treasury_Calculator/actions/workflows/quality_check.yml)
[![Scheduled Scrape](https://github.com/Al-QaTari/Treasury_Calculator/actions/workflows/scheduled_scrape.yml/badge.svg)](https://github.com/Al-QaTari/Treasury_Calculator/actions/workflows/scheduled_scrape.yml)
[![Made with Streamlit](https://img.shields.io/badge/Made_with-Streamlit-FF4B4B?logo=streamlit)](https://streamlit.io)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Al-QaTari/Treasury_Calculator/blob/main/LICENSE)

تطبيق ويب تفاعلي ومفتوح المصدر، تم بناؤه باستخدام Streamlit لمساعدة المستثمرين في السوق المصري على حساب وتحليل عوائد أذون الخزانة. يقوم التطبيق بجلب أحدث بيانات العطاءات بشكل آلي من موقع البنك المركزي المصري ويوفر أدوات حسابية دقيقة لاتخاذ قرارات استثمارية مدروسة.

---

![صورة متحركة للتطبيق](https://user-images.githubusercontent.com/8752322/232296180-73897255-c58d-4075-b3a6-57d2e9644558.gif)

---
## ✨ الميزات الرئيسية

- **جلب آلي للبيانات**: سحب أحدث بيانات عطاءات أذون الخزانة مباشرة من **موقع البنك المركزي المصري** لضمان دقة الأرقام.
- **واجهة مستخدم تفاعلية**: تصميم واضح وسهل الاستخدام يعرض أحدث العوائد ويقدم حاسبات متقدمة.
- **حاسبة العائد الأساسية**: لحساب صافي الربح المتوقع ونسبة العائد الفعلية عند الشراء والاحتفاظ حتى تاريخ الاستحقاق.
- **حاسبة البيع الثانوي**: أداة قوية لتحليل قرار البيع المبكر في السوق الثانوي، وحساب الربح أو الخسارة المحتملة.
- **قاعدة بيانات تاريخية**: حفظ البيانات تلقائيًا في قاعدة بيانات SQLite لتتبع التغيرات في العوائد مع مرور الوقت.
- **شرح مفصل**: قسم للمساعدة يشرح المفاهيم المالية الأساسية مثل الفرق بين العائد والفائدة وكيفية عمل الحاسبات.

---

## 🛠️ التقنيات المستخدمة
- **Streamlit**: لإنشاء واجهة المستخدم التفاعلية للتطبيق.
- **Pandas**: لتحليل ومعالجة البيانات المالية.
- **BeautifulSoup & Requests**: لجلب البيانات (Web Scraping) من موقع البنك المركزي.
- **SQLite**: لتخزين البيانات التاريخية للعطاءات.
- **GitHub Actions**: لإجراء فحص جودة الكود وجلب البيانات بشكل دوري تلقائيًا.

---

## 🚀 التشغيل المحلي

اتبع هذه الخطوات لتشغيل المشروع على جهازك.

### 1. المتطلبات الأساسية
- Python 3.8 أو أحدث.
- متصفح Google Chrome أو Brave مثبت على جهازك.

### 2. تثبيت المشروع
```bash
# انسخ المستودع إلى جهازك
git clone [https://github.com/Al-QaTari/Treasury_Calculator.git](https://github.com/Al-QaTari/Treasury_Calculator.git)

# ادخل إلى مجلد المشروع
cd Treasury_Calculator

# (مستحسن) أنشئ بيئة افتراضية لتثبيت المكتبات
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# قم بتثبيت المكتبات المطلوبة
pip install -r requirements.txt
3. تحديث البيانات (خطوة هامة جدًا)
⚠️ قبل تشغيل التطبيق لأول مرة، يجب تشغيل سكربت تحديث البيانات لجلب أحدث العوائد من البنك المركزي.

Bash

python update_data.py
هذه العملية قد تستغرق دقيقة أو اثنتين في المرة الأولى.

4. تشغيل التطبيق
بعد اكتمال تحديث البيانات، يمكنك الآن تشغيل تطبيق Streamlit.

Bash

streamlit run app.py
سيفتح التطبيق تلقائيًا في متصفحك.

📁 هيكل المشروع
Treasury_Calculator/
│
├── css/
│   └── style.css           # ملف التنسيقات (CSS)
├── app.py                  # التطبيق الرئيسي وواجهة المستخدم (Streamlit)
├── cbe_scraper.py          # منطق جلب البيانات من موقع البنك المركزي
├── calculations.py         # الدوال الخاصة بالعمليات الحسابية المالية
├── db_manager.py           # كلاس لإدارة قاعدة البيانات (SQLite)
├── constants.py            # جميع الثوابت والمتغيرات المركزية
├── utils.py                # دوال مساعدة (مثل معالجة النصوص)
├── update_data.py          # سكربت لتشغيل عملية تحديث البيانات
├── requirements.txt        # قائمة المكتبات المطلوبة للمشروع
├── LICENSE                 # ملف الترخيص الخاص بالمشروع
├── .gitignore              # لتجاهل الملفات غير المرغوب فيها
└── README.md               # ملف التوثيق هذا
🤝 للمساهمة
نرحب بجميع المساهمات لتحسين هذا المشروع. إذا كانت لديك فكرة رائعة أو إصلاح لخطأ ما، فلا تتردد في:

فتح Issue لمناقشة التغيير المقترح.

عمل Fork للمستودع وتقديم Pull Request.

📄 الترخيص
هذا المشروع مرخص تحت رخصة MIT. انظر ملف LICENSE للمزيد من التفاصيل.

⚠️ إخلاء مسؤولية
هذا التطبيق هو أداة إرشادية فقط، والأرقام الناتجة هي تقديرات بناءً على البيانات المتاحة. للحصول على أرقام نهائية ودقيقة وقرارات استثمارية، يرجى الرجوع دائمًا إلى البنك أو المؤسسة المالية التي تتعامل معها.
