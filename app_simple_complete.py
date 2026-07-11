# app_simple_complete.py
# ============================================================
# نسخه کامل - همه فازها با سوالات در Sidebar
# ============================================================

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
import re

# ============================================================
# بخش ۱: سوالات نمونه برای همه فازها
# ============================================================

QUESTIONS = {
    "phase1": [
        "فروش ماه گذشته چقدر بود؟",
        "محصولات پرفروش کدامند؟",
        "موجودی انبار چقدر است؟",
        "بهترین کالا از بابت ریال فروش کدام است؟"
    ],
    "phase2": [
        "پرفروش‌ترین محصولات کدامند؟",
        "فروش هر استان چقدر است؟",
        "روند فروش ماهانه چگونه است؟",
        "کدام مشتری بیشترین خرید را داشته؟"
    ],
    "phase3": [
        "📈 تحلیل روند فروش",
        "🔗 تحلیل علی فروش",
        "🛒 تحلیل سبد خرید"
    ],
    "phase4": [
        "📈 پیش‌بینی فروش ماه آینده",
        "🎯 شبیه‌سازی کاهش قیمت",
        "⚠️ تشخیص ناهنجاری‌ها"
    ],
    "phase5": [
        "😊 تحلیل احساسات مشتریان",
        "📄 گزارش روزانه فروش"
    ]
}

# ============================================================
# بخش ۲: کلاس Semantic (بهبود یافته)
# ============================================================

class SimpleSemantic:
    def __init__(self):
        self.keywords = {
            'فروش': ['فروش', 'درآمد', 'revenue', 'ریال فروش', 'مبلغ فروش'],
            'محصول': ['محصول', 'کالا', 'product', 'پرفروش', 'بهترین کالا'],
            'موجودی': ['موجودی', 'انبار', 'stock', 'ذخیره'],
            'مشتری': ['مشتری', 'خریدار', 'customer', 'مشتریان'],
            'سود': ['سود', 'profit', 'حاشیه سود', 'سودآوری']
        }
        
        self.time_words = ['امروز', 'دیروز', 'ماه', 'سال', 'هفته', 'گذشته', 'ماهانه']
    
    def analyze(self, text):
        if not text:
            return {'error': 'متن خالی است'}
        
        text_lower = text.lower()
        detected = []
        
        # تشخیص مفاهیم
        for concept, words in self.keywords.items():
            for word in words:
                if word in text_lower:
                    detected.append({'concept': concept, 'confidence': 0.8})
                    break
        
        # تشخیص زمان
        time_detected = None
        for t in self.time_words:
            if t in text_lower:
                time_detected = t
                break
        
        # تشخیص قصد
        if any(w in text_lower for w in ['فروش', 'درآمد', 'ریال']):
            intent = 'sales_analysis'
        elif any(w in text_lower for w in ['موجودی', 'انبار']):
            intent = 'inventory_check'
        elif any(w in text_lower for w in ['سود', 'حاشیه']):
            intent = 'profit_analysis'
        elif any(w in text_lower for w in ['پیش‌بینی', 'آینده']):
            intent = 'prediction'
        elif any(w in text_lower for w in ['مقایسه', 'نسبت']):
            intent = 'comparison'
        else:
            intent = 'general'
        
        confidence = min(1.0, len(detected) / 2 + 0.2)
        
        return {
            'detected_concepts': detected,
            'intent': intent,
            'confidence': confidence,
            'time': time_detected
        }

# ============================================================
# بخش ۳: کلاس اصلی
# ============================================================

class AppCore:
    def __init__(self):
        self.semantic = SimpleSemantic()
        self.db_path = 'fmcg_distribution_complete.db'
    
    def load_data(self):
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
                SELECT 
                    f.date_id as date,
                    f.product_id,
                    f.quantity as sales,
                    f.unit_price as price,
                    f.net_amount as revenue,
                    p.product_name,
                    p.category,
                    p.brand
                FROM fact_sales f
                JOIN dim_product p ON f.product_id = p.product_id
                ORDER BY f.date_id
                LIMIT 5000
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except:
            return self._sample_data()
    
    def _sample_data(self):
        dates = pd.date_range(start='2026-01-01', periods=30, freq='D')
        return pd.DataFrame({
            'date': dates,
            'product_id': [1,2,3]*10,
            'sales': [50,30,20]*10,
            'price': [50,30,20]*10,
            'revenue': [2500,900,400]*10,
            'product_name': ['محصول 1','محصول 2','محصول 3']*10,
            'category': ['دسته 1','دسته 2','دسته 3']*10,
            'brand': ['برند A','برند B','برند C']*10
        })

# ============================================================
# بخش ۴: Sidebar با سوالات همه فازها
# ============================================================

def render_sidebar():
    """رندر Sidebar با سوالات کلیکی همه فازها"""
    with st.sidebar:
        st.markdown("## 📌 سوالات سریع")
        st.markdown("---")
        
        # فاز ۱
        st.markdown("### 🧠 فاز ۱: Semantic")
        for i, q in enumerate(QUESTIONS["phase1"]):
            if st.button(f"🔹 {q}", key=f"p1_q_{i}", use_container_width=True):
                st.session_state['p1_query'] = q
                st.session_state['p1_auto_run'] = True
        
        st.markdown("---")
        
        # فاز ۲
        st.markdown("### 🗂️ فاز ۲: Query")
        for i, q in enumerate(QUESTIONS["phase2"]):
            if st.button(f"🔹 {q}", key=f"p2_q_{i}", use_container_width=True):
                st.session_state['p2_query'] = q
                st.session_state['p2_auto_run'] = True
        
        st.markdown("---")
        
        # فاز ۳
        st.markdown("### 📊 فاز ۳: Analytical")
        for i, q in enumerate(QUESTIONS["phase3"]):
            if st.button(f"🔹 {q}", key=f"p3_q_{i}", use_container_width=True):
                st.session_state['p3_action'] = q
                st.session_state['p3_auto_run'] = True
        
        st.markdown("---")
        
        # فاز ۴
        st.markdown("### 🔮 فاز ۴: Predictive")
        for i, q in enumerate(QUESTIONS["phase4"]):
            if st.button(f"🔹 {q}", key=f"p4_q_{i}", use_container_width=True):
                st.session_state['p4_action'] = q
                st.session_state['p4_auto_run'] = True
        
        st.markdown("---")
        
        # فاز ۵
        st.markdown("### 😊 فاز ۵: New Features")
        for i, q in enumerate(QUESTIONS["phase5"]):
            if st.button(f"🔹 {q}", key=f"p5_q_{i}", use_container_width=True):
                st.session_state['p5_action'] = q
                st.session_state['p5_auto_run'] = True
        
        st.markdown("---")
        st.caption(f"📊 {datetime.now().strftime('%H:%M:%S')}")

# ============================================================
# بخش ۵: نمایش فاز ۱
# ============================================================

def render_phase1(app):
    st.subheader("🧠 فاز ۱: Semantic Layer")
    st.caption("تشخیص مفاهیم و قصد از متن سوال")
    
    if 'p1_query' not in st.session_state:
        st.session_state['p1_query'] = ''
    if 'p1_result' not in st.session_state:
        st.session_state['p1_result'] = None
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        query = st.text_input(
            "📝 متن خود را وارد کنید:",
            value=st.session_state.get('p1_query', ''),
            key="p1_input",
            placeholder="مثال: فروش ماه گذشته چقدر بود؟"
        )
        if query and query != st.session_state.get('p1_query'):
            st.session_state['p1_query'] = query
    
    with col2:
        if st.button("🔍 تحلیل", key="p1_btn", use_container_width=True):
            if query:
                result = app.semantic.analyze(query)
                st.session_state['p1_result'] = result
                st.session_state['p1_auto_run'] = False
    
    if st.session_state.get('p1_auto_run', False) and st.session_state.get('p1_query'):
        query = st.session_state['p1_query']
        result = app.semantic.analyze(query)
        st.session_state['p1_result'] = result
        st.session_state['p1_auto_run'] = False
    
    if st.session_state.get('p1_result'):
        result = st.session_state['p1_result']
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 تحلیل معنایی:**")
            concepts = result.get('detected_concepts', [])
            if concepts:
                for c in concepts:
                    st.success(f"✅ {c.get('concept', 'نامشخص')}")
            else:
                st.warning("⚠️ هیچ مفهومی تشخیص داده نشد")
            
            if result.get('time'):
                st.info(f"📅 زمان: {result['time']}")
            
            st.metric("🎯 قصد کلی", result.get('intent', 'نامشخص'))
            st.caption(f"اطمینان: {result.get('confidence', 0)*100:.0f}%")
        
        with col2:
            st.markdown("**📊 توضیح:**")
            intent = result.get('intent', '')
            descriptions = {
                'sales_analysis': 'سوال درباره فروش و درآمد',
                'inventory_check': 'سوال درباره موجودی انبار',
                'profit_analysis': 'سوال درباره سود',
                'prediction': 'سوال درباره پیش‌بینی',
                'comparison': 'سوال مقایسه‌ای',
                'general': 'سوال عمومی'
            }
            st.info(descriptions.get(intent, 'سوال عمومی'))

# ============================================================
# بخش ۶: نمایش فاز ۲
# ============================================================

def render_phase2(app):
    st.subheader("🗂️ فاز ۲: Query Planner")
    st.caption("برنامه‌ریزی کوئری و نمایش نتایج")
    
    if 'p2_query' not in st.session_state:
        st.session_state['p2_query'] = ''
    if 'p2_result' not in st.session_state:
        st.session_state['p2_result'] = None
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        query = st.text_input(
            "📝 سوال خود را وارد کنید:",
            value=st.session_state.get('p2_query', ''),
            key="p2_input",
            placeholder="مثال: محصولات پرفروش کدامند؟"
        )
        if query and query != st.session_state.get('p2_query'):
            st.session_state['p2_query'] = query
    
    with col2:
        if st.button("🔍 اجرا", key="p2_btn", use_container_width=True):
            if query:
                try:
                    sql = "SELECT * FROM fact_sales LIMIT 10"
                    st.session_state['p2_result'] = {'sql': sql, 'query': query}
                except Exception as e:
                    st.error(f"خطا: {e}")
    
    if st.session_state.get('p2_auto_run', False) and st.session_state.get('p2_query'):
        query = st.session_state['p2_query']
        try:
            sql = "SELECT * FROM fact_sales LIMIT 10"
            st.session_state['p2_result'] = {'sql': sql, 'query': query}
            st.session_state['p2_auto_run'] = False
        except Exception as e:
            st.error(f"خطا: {e}")
    
    if st.session_state.get('p2_result'):
        result = st.session_state['p2_result']
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📄 کوئری:**")
            st.code(result.get('sql', ''), language='sql')
        
        with col2:
            st.markdown("**📊 نتایج:**")
            try:
                df = app.load_data()
                if not df.empty:
                    st.dataframe(df.head(10), use_container_width=True)
                    st.caption(f"📌 {len(df)} رکورد")
                else:
                    st.info("نتیجه‌ای یافت نشد")
            except Exception as e:
                st.warning(f"⚠️ {e}")

# ============================================================
# بخش ۷: نمایش فاز ۳
# ============================================================

def render_phase3(app):
    st.subheader("📊 فاز ۳: Analytical Engine")
    st.caption("تحلیل روند، علی و سبد خرید")
    
    if 'p3_result' not in st.session_state:
        st.session_state['p3_result'] = None
    if 'p3_action' not in st.session_state:
        st.session_state['p3_action'] = ''
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📈 تحلیل روند", key="p3_trend", use_container_width=True):
            df = app.load_data()
            if not df.empty:
                daily = df.groupby('date')['sales'].sum()
                trend = 'صعودی' if len(daily) > 1 and daily.iloc[-1] > daily.iloc[0] else 'نزولی'
                st.session_state['p3_result'] = {
                    'type': 'trend',
                    'trend': trend,
                    'change': ((daily.iloc[-1] - daily.iloc[0]) / daily.iloc[0] * 100) if daily.iloc[0] > 0 else 0
                }
    
    with col2:
        if st.button("🔗 تحلیل علی", key="p3_causal", use_container_width=True):
            df = app.load_data()
            if not df.empty and 'price' in df.columns and 'sales' in df.columns:
                corr = df['price'].corr(df['sales'])
                st.session_state['p3_result'] = {
                    'type': 'causal',
                    'correlation': corr,
                    'insight': '💰 قیمت بالا با فروش بالا همراه است' if corr > 0.3 else ('⚠️ قیمت بالا باعث کاهش فروش شده است' if corr < -0.3 else '➡️ رابطه معناداری وجود ندارد')
                }
    
    with col3:
        if st.button("🛒 سبد خرید", key="p3_basket", use_container_width=True):
            df = app.load_data()
            if not df.empty:
                top = df.groupby('product_name')['sales'].sum().nlargest(5)
                st.session_state['p3_result'] = {
                    'type': 'basket',
                    'top_products': top.to_dict()
                }
    
    # اجرای خودکار از Sidebar
    if st.session_state.get('p3_auto_run', False) and st.session_state.get('p3_action'):
        action = st.session_state['p3_action']
        df = app.load_data()
        if not df.empty:
            if "روند" in action:
                daily = df.groupby('date')['sales'].sum()
                trend = 'صعودی' if len(daily) > 1 and daily.iloc[-1] > daily.iloc[0] else 'نزولی'
                st.session_state['p3_result'] = {
                    'type': 'trend',
                    'trend': trend,
                    'change': ((daily.iloc[-1] - daily.iloc[0]) / daily.iloc[0] * 100) if daily.iloc[0] > 0 else 0
                }
            elif "علی" in action:
                corr = df['price'].corr(df['sales']) if 'price' in df.columns else 0
                st.session_state['p3_result'] = {
                    'type': 'causal',
                    'correlation': corr,
                    'insight': '💰 قیمت بالا با فروش بالا همراه است' if corr > 0.3 else ('⚠️ قیمت بالا باعث کاهش فروش شده است' if corr < -0.3 else '➡️ رابطه معناداری وجود ندارد')
                }
            elif "سبد" in action:
                top = df.groupby('product_name')['sales'].sum().nlargest(5)
                st.session_state['p3_result'] = {
                    'type': 'basket',
                    'top_products': top.to_dict()
                }
        st.session_state['p3_auto_run'] = False
    
    if st.session_state.get('p3_result'):
        result = st.session_state['p3_result']
        
        if result.get('type') == 'trend':
            st.success(f"✅ روند: {result['trend']}")
            st.metric("تغییر درصدی", f"{result['change']:.1f}%")
        
        elif result.get('type') == 'causal':
            st.metric("همبستگی قیمت-فروش", f"{result['correlation']:.2f}")
            st.info(result['insight'])
        
        elif result.get('type') == 'basket':
            st.write("🏆 محصولات پرفروش:")
            for name, val in result.get('top_products', {}).items():
                st.write(f"- {name}: {val}")

# ============================================================
# بخش ۸: نمایش فاز ۴
# ============================================================

def render_phase4(app):
    st.subheader("🔮 فاز ۴: Predictive Engine")
    st.caption("پیش‌بینی، شبیه‌سازی و تشخیص ناهنجاری")
    
    if 'p4_result' not in st.session_state:
        st.session_state['p4_result'] = None
    if 'p4_action' not in st.session_state:
        st.session_state['p4_action'] = ''
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        months = st.number_input("تعداد ماه‌ها", 1, 12, 3, key="p4_months")
        if st.button("📈 پیش‌بینی", key="p4_forecast", use_container_width=True):
            df = app.load_data()
            if not df.empty:
                avg = df['sales'].mean()
                st.session_state['p4_result'] = {
                    'type': 'forecast',
                    'avg': avg,
                    'next': avg * 1.05,
                    'months': months
                }
    
    with col2:
        change = st.slider("تغییر قیمت (%)", -30, 30, -10, key="p4_change")
        if st.button("🎯 شبیه‌سازی", key="p4_sim", use_container_width=True):
            df = app.load_data()
            if not df.empty:
                current_profit = (df['sales'] * (df['price'] - df['price'] * 0.6)).sum()
                new_profit = current_profit * (1 + change / 100 * 0.5)
                st.session_state['p4_result'] = {
                    'type': 'simulation',
                    'current_profit': current_profit,
                    'new_profit': new_profit,
                    'change': change
                }
    
    with col3:
        if st.button("⚠️ ناهنجاری", key="p4_anomaly", use_container_width=True):
            df = app.load_data()
            if not df.empty:
                Q1 = df['sales'].quantile(0.25)
                Q3 = df['sales'].quantile(0.75)
                IQR = Q3 - Q1
                outliers = df[(df['sales'] < Q1 - 1.5*IQR) | (df['sales'] > Q3 + 1.5*IQR)]
                st.session_state['p4_result'] = {
                    'type': 'anomaly',
                    'count': len(outliers),
                    'outliers': outliers[['date', 'sales']].head(10) if not outliers.empty else None
                }
    
    # اجرای خودکار از Sidebar
    if st.session_state.get('p4_auto_run', False) and st.session_state.get('p4_action'):
        action = st.session_state['p4_action']
        df = app.load_data()
        if not df.empty:
            if "پیش‌بینی" in action:
                avg = df['sales'].mean()
                st.session_state['p4_result'] = {
                    'type': 'forecast',
                    'avg': avg,
                    'next': avg * 1.05,
                    'months': 3
                }
            elif "شبیه‌سازی" in action:
                current_profit = (df['sales'] * (df['price'] - df['price'] * 0.6)).sum()
                new_profit = current_profit * (1 + -10 / 100 * 0.5)
                st.session_state['p4_result'] = {
                    'type': 'simulation',
                    'current_profit': current_profit,
                    'new_profit': new_profit,
                    'change': -10
                }
            elif "ناهنجاری" in action:
                Q1 = df['sales'].quantile(0.25)
                Q3 = df['sales'].quantile(0.75)
                IQR = Q3 - Q1
                outliers = df[(df['sales'] < Q1 - 1.5*IQR) | (df['sales'] > Q3 + 1.5*IQR)]
                st.session_state['p4_result'] = {
                    'type': 'anomaly',
                    'count': len(outliers),
                    'outliers': outliers[['date', 'sales']].head(10) if not outliers.empty else None
                }
        st.session_state['p4_auto_run'] = False
    
    if st.session_state.get('p4_result'):
        result = st.session_state['p4_result']
        
        if result.get('type') == 'forecast':
            st.success(f"✅ پیش‌بینی برای {result['months']} ماه آینده")
            st.metric("میانگین فروش روزانه", f"{result['avg']:,.0f}")
            st.metric("پیش‌بینی فردا", f"{result['next']:,.0f}")
        
        elif result.get('type') == 'simulation':
            st.metric("سود فعلی", f"{result['current_profit']:,.0f}")
            st.metric("سود جدید", f"{result['new_profit']:,.0f}")
            change_pct = ((result['new_profit'] - result['current_profit']) / result['current_profit'] * 100) if result['current_profit'] > 0 else 0
            st.caption(f"تغییر سود: {change_pct:.1f}%")
        
        elif result.get('type') == 'anomaly':
            if result['count'] > 0:
                st.warning(f"⚠️ {result['count']} ناهنجاری شناسایی شد")
                if result['outliers'] is not None and not result['outliers'].empty:
                    st.dataframe(result['outliers'])
            else:
                st.success("✅ هیچ ناهنجاری شناسایی نشد")

# ============================================================
# بخش ۹: نمایش فاز ۵
# ============================================================

def render_phase5(app):
    st.subheader("😊 فاز ۵: New Features")
    st.caption("تحلیل احساسات، هشدارها و گزارش‌گیری")
    
    if 'p5_result' not in st.session_state:
        st.session_state['p5_result'] = None
    if 'p5_action' not in st.session_state:
        st.session_state['p5_action'] = ''
    
    tab1, tab2 = st.tabs(["😊 احساسات", "📄 گزارش"])
    
    with tab1:
        st.markdown("**تحلیل احساسات نظرات مشتریان**")
        
        sample_reviews = [
            "کیفیت عالی، خیلی راضی بودم از خرید",
            "جنس خوبیه ولی قیمتش یه کم بالاست",
            "بدترین محصولی که خریدم، پشیمون شدم",
            "بی‌نظیر، به همه دوستانم پیشنهاد کردم"
        ]
        
        for i, review in enumerate(sample_reviews):
            st.write(f"📝 {review}")
        
        if st.button("📊 تحلیل احساسات", key="p5_sentiment_btn", use_container_width=True):
            # تحلیل ساده
            positive = ["عالی", "راضی", "بی‌نظیر", "پیشنهاد"]
            negative = ["بدترین", "پشیمون", "خراب"]
            
            results = []
            for review in sample_reviews:
                sentiment = "مثبت" if any(w in review for w in positive) else ("منفی" if any(w in review for w in negative) else "خنثی")
                results.append({"نظر": review[:30] + "...", "احساسات": sentiment})
            
            st.session_state['p5_result'] = {
                'type': 'sentiment',
                'results': results
            }
        
        if st.session_state.get('p5_auto_run', False) and st.session_state.get('p5_action'):
            if "احساسات" in st.session_state['p5_action']:
                positive = ["عالی", "راضی", "بی‌نظیر", "پیشنهاد"]
                negative = ["بدترین", "پشیمون", "خراب"]
                sample_reviews = [
                    "کیفیت عالی، خیلی راضی بودم از خرید",
                    "جنس خوبیه ولی قیمتش یه کم بالاست",
                    "بدترین محصولی که خریدم، پشیمون شدم",
                    "بی‌نظیر، به همه دوستانم پیشنهاد کردم"
                ]
                results = []
                for review in sample_reviews:
                    sentiment = "مثبت" if any(w in review for w in positive) else ("منفی" if any(w in review for w in negative) else "خنثی")
                    results.append({"نظر": review[:30] + "...", "احساسات": sentiment})
                st.session_state['p5_result'] = {
                    'type': 'sentiment',
                    'results': results
                }
            st.session_state['p5_auto_run'] = False
    
    with tab2:
        st.markdown("**📄 گزارش روزانه فروش**")
        
        df = app.load_data()
        if not df.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("💰 فروش کل", f"{df['sales'].sum():,.0f}")
            col2.metric("📦 تعداد سفارشات", f"{len(df):,}")
            col3.metric("🏷️ محصولات", f"{df['product_id'].nunique()}")
            
            if st.button("📊 تولید گزارش کامل", key="p5_report_btn", use_container_width=True):
                st.session_state['p5_result'] = {
                    'type': 'report',
                    'total_sales': df['sales'].sum(),
                    'total_orders': len(df),
                    'unique_products': df['product_id'].nunique(),
                    'avg_price': df['price'].mean()
                }
        
        if st.session_state.get('p5_result') and st.session_state['p5_result'].get('type') == 'report':
            result = st.session_state['p5_result']
            st.markdown("---")
            st.markdown("**📊 خلاصه گزارش:**")
            st.write(f"- فروش کل: {result['total_sales']:,.0f}")
            st.write(f"- تعداد سفارشات: {result['total_orders']}")
            st.write(f"- محصولات منحصر‌به‌فرد: {result['unique_products']}")
            st.write(f"- میانگین قیمت: {result['avg_price']:,.0f}")

# ============================================================
# بخش ۱۰: داشبورد
# ============================================================

def render_dashboard(app):
    st.subheader("📊 داشبورد جامع")
    
    df = app.load_data()
    
    if df.empty:
        st.warning("⚠️ داده‌ای برای نمایش وجود ندارد")
        return
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 فروش کل", f"{df['sales'].sum():,.0f}")
    c2.metric("📦 تعداد سفارشات", f"{len(df):,}")
    c3.metric("🏷️ محصولات", f"{df['product_id'].nunique()}")
    c4.metric("💵 میانگین قیمت", f"{df['price'].mean():,.0f}")
    
    st.markdown("---")
    
    st.subheader("📈 روند فروش")
    try:
        daily = df.groupby('date')['sales'].sum().reset_index()
        fig = px.line(daily, x='date', y='sales', title="فروش روزانه")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"خطا: {e}")
    
    if 'category' in df.columns:
        col1, col2 = st.columns(2)
        with col1:
            try:
                cat = df.groupby('category')['sales'].sum().reset_index()
                fig = px.pie(cat, values='sales', names='category', title="سهم دسته‌بندی‌ها")
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
            except:
                pass
        
        with col2:
            try:
                top = df.groupby('product_name')['sales'].sum().nlargest(10).reset_index()
                fig = px.bar(top, x='product_name', y='sales', title="۱۰ محصول پرفروش")
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
            except:
                pass

# ============================================================
# بخش ۱۱: اجرا
# ============================================================

def main():
    st.set_page_config(
        page_title="📊 سیستم جامع تحلیل فروش FMCG",
        page_icon="📈",
        layout="wide"
    )
    
    # مقداردهی اولیه
    if 'p1_query' not in st.session_state:
        st.session_state['p1_query'] = ''
    if 'p1_auto_run' not in st.session_state:
        st.session_state['p1_auto_run'] = False
    if 'p2_query' not in st.session_state:
        st.session_state['p2_query'] = ''
    if 'p2_auto_run' not in st.session_state:
        st.session_state['p2_auto_run'] = False
    if 'p3_auto_run' not in st.session_state:
        st.session_state['p3_auto_run'] = False
    if 'p4_auto_run' not in st.session_state:
        st.session_state['p4_auto_run'] = False
    if 'p5_auto_run' not in st.session_state:
        st.session_state['p5_auto_run'] = False
    if 'p3_action' not in st.session_state:
        st.session_state['p3_action'] = ''
    if 'p4_action' not in st.session_state:
        st.session_state['p4_action'] = ''
    if 'p5_action' not in st.session_state:
        st.session_state['p5_action'] = ''
    
    render_sidebar()
    
    st.title("📊 سیستم جامع تحلیل فروش FMCG")
    st.caption("نسخه 2.0.0 | Enterprise Edition")
    st.markdown("---")
    
    app = AppCore()
    
    tabs = st.tabs([
        "📊 داشبورد",
        "🧠 فاز ۱",
        "🗂️ فاز ۲",
        "📊 فاز ۳",
        "🔮 فاز ۴",
        "😊 فاز ۵"
    ])
    
    with tabs[0]:
        render_dashboard(app)
    with tabs[1]:
        render_phase1(app)
    with tabs[2]:
        render_phase2(app)
    with tabs[3]:
        render_phase3(app)
    with tabs[4]:
        render_phase4(app)
    with tabs[5]:
        render_phase5(app)

if __name__ == "__main__":
    main()