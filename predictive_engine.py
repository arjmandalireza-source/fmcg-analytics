# predictive_engine.py
# ============================================================
# موتور پیش‌بینی و تصمیم‌سازی - فاز ۴
# ============================================================

import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
import re
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline

class PredictiveEngine:
    def __init__(self):
        self.conn = sqlite3.connect('fmcg_distribution_complete.db')
        self.cursor = self.conn.cursor()
    
    # ============================================================
    # ۱. پیش‌بینی فروش (Forecasting)
    # ============================================================
    def forecast_sales(self, months_ahead: int = 3, 
                       product_id: int = None, 
                       category: str = None,
                       region: str = None) -> dict:
        """پیش‌بینی فروش با استفاده از رگرسیون خطی"""
        
        result = {
            "type": "forecast",
            "insights": [],
            "data": None,
            "forecast": None,
            "recommendations": []
        }
        
        # ۱.۱ دریافت داده‌های تاریخی
        query = """
        SELECT 
            strftime('%Y-%m', date_id) as month,
            SUM(net_amount) as total_sales
        FROM fact_sales fs
        """
        
        joins = []
        where = []
        
        if product_id:
            where.append(f"fs.product_id = {product_id}")
        if category:
            joins.append("JOIN dim_product p ON fs.product_id = p.product_id")
            where.append(f"p.category = '{category}'")
        if region:
            joins.append("JOIN dim_customer c ON fs.customer_id = c.customer_id")
            joins.append("JOIN dim_geography g ON c.region_id = g.geo_id")
            where.append(f"g.province_name = '{region}'")
        
        if joins:
            query += " " + " ".join(joins)
        if where:
            query += " WHERE " + " AND ".join(where)
        
        query += " GROUP BY month ORDER BY month"
        
        try:
            df = pd.read_sql(query, self.conn)
        except Exception as e:
            return {"error": f"خطا در دریافت داده: {str(e)}"}
        
        if df.empty or len(df) < 3:
            return {"error": "داده‌های کافی برای پیش‌بینی وجود ندارد (حداقل ۳ ماه داده نیاز است)"}
        
        result["data"] = df
        
        # ۱.۲ آماده‌سازی داده برای مدل
        df['month_num'] = range(1, len(df) + 1)
        X = df[['month_num']].values
        y = df['total_sales'].values
        
        # ۱.۳ آموزش مدل
        try:
            model = make_pipeline(PolynomialFeatures(2), LinearRegression())
            model.fit(X, y)
        except Exception as e:
            return {"error": f"خطا در آموزش مدل: {str(e)}"}
        
        # ۱.۴ پیش‌بینی
        future_months = np.array(range(len(df) + 1, len(df) + months_ahead + 1)).reshape(-1, 1)
        forecast_values = model.predict(future_months)
        
        # ۱.۵ محاسبه رشد
        last_value = y[-1] if len(y) > 0 else 0
        avg_growth = ((y[-1] - y[0]) / y[0] * 100) if y[0] > 0 else 0
        
        # ۱.۶ تولید بینش
        result["forecast"] = {
            "months": [f"ماه {i+1}" for i in range(months_ahead)],
            "values": forecast_values.tolist(),
            "avg_growth": avg_growth,
            "last_value": last_value
        }
        
        result["insights"].append(f"📈 پیش‌بینی فروش برای {months_ahead} ماه آینده:")
        for i, val in enumerate(forecast_values):
            result["insights"].append(f"  - ماه {i+1}: {val:,.0f} تومان")
        
        # ۱.۷ پیشنهادات
        if avg_growth > 0:
            result["recommendations"].append("✅ روند فروش صعودی است. استراتژی فعلی را ادامه دهید.")
        else:
            result["recommendations"].append("⚠️ روند فروش نزولی است. نیاز به بررسی علت و ارائه راهکار دارد.")
        
        if forecast_values[-1] < last_value:
            result["recommendations"].append("🔴 پیش‌بینی کاهش فروش در ماه آینده. برنامه ریزی برای جبران انجام شود.")
        
        return result
    
    # ============================================================
    # ۲. تحلیل What-if (شبیه‌سازی سناریو)
    # ============================================================
    def what_if_analysis(self, scenario: str = "price_change", 
                        change_percent: float = -10,
                        product_id: int = None,
                        category: str = None) -> dict:
        """شبیه‌سازی سناریوهای مختلف"""
        
        result = {
            "type": "what_if",
            "insights": [],
            "scenario": scenario,
            "current": {},
            "simulated": {},
            "recommendations": []
        }
        
        # دریافت داده‌های فعلی
        query = """
        SELECT 
            SUM(quantity) as total_quantity,
            ROUND(AVG(unit_price), 2) as avg_price,
            ROUND(SUM(net_amount), 0) as total_sales,
            ROUND(SUM(gross_profit), 0) as total_profit
        FROM fact_sales
        WHERE 1=1
        """
        if product_id:
            query += f" AND product_id = {product_id}"
        if category:
            query += f" AND product_id IN (SELECT product_id FROM dim_product WHERE category = '{category}')"
        
        df = pd.read_sql(query, self.conn)
        
        if df.empty:
            return {"error": "داده‌های کافی برای شبیه‌سازی وجود ندارد."}
        
        current = {
            "quantity": df['total_quantity'].iloc[0],
            "avg_price": df['avg_price'].iloc[0],
            "sales": df['total_sales'].iloc[0],
            "profit": df['total_profit'].iloc[0]
        }
        
        result["current"] = current
        
        # شبیه‌سازی
        elasticity = -0.5
        new_price = current['avg_price'] * (1 + change_percent / 100)
        quantity_change = elasticity * change_percent
        new_quantity = current['quantity'] * (1 + quantity_change / 100)
        
        avg_cost = (current['sales'] - current['profit']) / current['quantity'] if current['quantity'] > 0 else 0
        new_sales = new_quantity * new_price
        new_profit = new_sales - (new_quantity * avg_cost)
        
        simulated = {
            "new_price": new_price,
            "new_quantity": new_quantity,
            "new_sales": new_sales,
            "new_profit": new_profit
        }
        
        result["simulated"] = simulated
        
        # بینش
        profit_change = ((new_profit - current['profit']) / current['profit']) * 100 if current['profit'] > 0 else 0
        
        result["insights"].append(f"📊 تغییر قیمت: {change_percent}%")
        result["insights"].append(f"📈 تغییر سود: {profit_change:.2f}%")
        
        if profit_change > 0:
            result["recommendations"].append("✅ این تغییر قیمت باعث افزایش سود می‌شود. اجرا توصیه می‌شود.")
        else:
            result["recommendations"].append("⚠️ این تغییر قیمت باعث کاهش سود می‌شود. بهتر است اجرا نشود.")
        
        return result
    
    # ============================================================
    # ۳. تشخیص ناهنجاری (Anomaly Detection)
    # ============================================================
    def detect_anomalies(self, metric: str = "sales", 
                         threshold: float = 2.0,
                         days: int = 90) -> dict:
        """تشخیص ناهنجاری‌ها در داده‌های فروش"""
        
        result = {
            "type": "anomaly",
            "insights": [],
            "anomalies": [],
            "recommendations": []
        }
        
        query = f"""
        SELECT 
            date_id,
            SUM(net_amount) as daily_sales
        FROM fact_sales
        WHERE date_id >= date('now', '-{days} days')
        GROUP BY date_id
        ORDER BY date_id
        """
        
        df = pd.read_sql(query, self.conn)
        
        if df.empty:
            return {"error": "داده‌های کافی برای تشخیص ناهنجاری وجود ندارد."}
        
        # محاسبه میانگین و انحراف معیار
        mean = df['daily_sales'].mean()
        std = df['daily_sales'].std()
        
        # تشخیص ناهنجاری‌ها
        df['z_score'] = (df['daily_sales'] - mean) / std
        anomalies = df[abs(df['z_score']) > threshold]
        
        if not anomalies.empty:
            result["anomalies"] = anomalies
            result["insights"].append(f"⚠️ {len(anomalies)} ناهنجاری شناسایی شد.")
            
            # پیشنهادات
            for _, row in anomalies.iterrows():
                if row['daily_sales'] > mean:
                    result["recommendations"].append(f"🔴 فروش {row['date_id']}: {row['daily_sales']:,.0f} تومان (بیش از حد معمول)")
                else:
                    result["recommendations"].append(f"🟡 فروش {row['date_id']}: {row['daily_sales']:,.0f} تومان (کمتر از حد معمول)")
        else:
            result["insights"].append("✅ هیچ ناهنجاری شناسایی نشد.")
        
        return result
    
    # ============================================================
    # ۴. تحلیل هوشمند ترکیبی فاز ۴
    # ============================================================
    def smart_analysis(self, question: str) -> dict:
        """تحلیل هوشمند بر اساس سوال کاربر - فاز ۴"""
        
        q = question.lower()
        result = None
        
        if "پیش‌بینی" in q or "forecast" in q or "آینده" in q:
            if "محصول" in q:
                # پیدا کردن نام محصول
                product_name = None
                for p in ["شیر", "ماست", "پنیر", "آب", "نوشابه", "چیپس"]:
                    if p in q:
                        product_name = p
                        break
                if product_name:
                    cursor = self.conn.cursor()
                    cursor.execute(f"SELECT product_id FROM dim_product WHERE product_name LIKE '%{product_name}%'")
                    pid = cursor.fetchone()
                    if pid:
                        result = self.forecast_sales(months_ahead=3, product_id=pid[0])
                    else:
                        result = self.forecast_sales(months_ahead=3)
                else:
                    result = self.forecast_sales(months_ahead=3)
            elif "استان" in q or "منطقه" in q:
                region = None
                for r in ["تهران", "اصفهان", "مشهد", "شیراز", "تبریز", "اهواز"]:
                    if r in q:
                        region = r
                        break
                result = self.forecast_sales(months_ahead=3, region=region)
            else:
                result = self.forecast_sales(months_ahead=3)
        
        elif "شبیه‌سازی" in q or "what-if" in q or "اگر" in q:
            change = -10
            if "۵" in q:
                change = -5
            elif "۱۵" in q:
                change = -15
            elif "افزایش" in q:
                change = 5
            
            if "تخفیف" in q:
                change = -15
            if "قیمت" in q:
                change = -10
            
            result = self.what_if_analysis(
                scenario="price_change",
                change_percent=change
            )
        
        elif "ناهنجاری" in q or "anomaly" in q or "غیرعادی" in q:
            result = self.detect_anomalies(days=90)
        
        else:
            result = {
                "type": "unknown",
                "insights": ["⚠️ نوع تحلیل تشخیص داده نشد. لطفاً یکی از این کلمات را استفاده کنید:\n- پیش‌بینی\n- شبیه‌سازی\n- ناهنجاری"]
            }
        
        return result
    
    def close(self):
        self.conn.close()


# ============================================================
# تابع اصلی تحلیل هوشمند فاز ۴
# ============================================================
def smart_analyze_phase4(question: str) -> dict:
    """تحلیل هوشمند با استفاده از فاز ۴"""
    
    engine = PredictiveEngine()
    result = engine.smart_analysis(question)
    engine.close()
    
    return {
        "question": question,
        "analysis": result
    }


if __name__ == "__main__":
    test_questions = [
        "پیش‌بینی فروش ماه آینده",
        "شبیه‌سازی کاهش ۱۰ درصدی قیمت بر فروش و سود",
        "تشخیص ناهنجاری‌های فروش در ۳ ماه اخیر"
    ]
    
    print("=" * 60)
    print("🧠 تست فاز ۴ - Predictive Engine")
    print("=" * 60)
    
    for q in test_questions:
        print(f"\n📝 سوال: {q}")
        result = smart_analyze_phase4(q)
        analysis = result["analysis"]
        print(f"  نوع تحلیل: {analysis.get('type', 'unknown')}")
        if "insights" in analysis:
            for insight in analysis["insights"]:
                print(f"  💡 {insight}")