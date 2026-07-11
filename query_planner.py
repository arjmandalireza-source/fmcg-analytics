# query_planner.py
# ============================================================
# برنامه‌ریز کوئری (Query Planner) - نسخه اصلاح شده
# ============================================================

import re
import pandas as pd
import sqlite3

# ============================================================
# ۱. توابع کمکی (جایگزین semantic_complete)
# ============================================================

def resolve_concept(question: str) -> str:
    """تشخیص مفهوم از سوال کاربر"""
    q = question.lower()
    concepts = {
        "فروش": ["فروش", "درآمد", "revenue"],
        "سود": ["سود", "profit"],
        "موجودی": ["موجودی", "انبار", "stock"],
        "محصول": ["محصول", "کالا", "product"],
        "مشتری": ["مشتری", "خریدار", "customer"],
        "ویزیت": ["ویزیت", "بازدید", "visit"],
        "تحویل": ["تحویل", "ارسال", "delivery"]
    }
    for concept, synonyms in concepts.items():
        for syn in synonyms:
            if syn in q:
                return concept
    return None

def get_semantic(concept: str) -> dict:
    """دریافت اطلاعات معنایی یک مفهوم"""
    semantic_data = {
        "فروش": {"table": "fact_sales", "column": "net_amount", "aggregation": "SUM"},
        "سود": {"table": "fact_sales", "column": "gross_profit", "aggregation": "SUM"},
        "موجودی": {"table": "fact_inventory", "column": "ending_balance", "aggregation": "SUM"},
        "محصول": {"table": "dim_product", "column": "product_name"},
        "مشتری": {"table": "dim_customer", "column": "customer_name"},
        "ویزیت": {"table": "fact_visits", "column": "visit_id", "aggregation": "COUNT"},
        "تحویل": {"table": "fact_deliveries", "column": "delivery_id", "aggregation": "COUNT"}
    }
    return semantic_data.get(concept, {})


class QueryPlanner:
    def __init__(self):
        # ============================================================
        # ۱. نگاشت ابعاد به ستون‌ها
        # ============================================================
        self.dimension_columns = {
            "استان": "dim_geography.province_name",
            "شهر": "dim_geography.city_name",
            "محصول": "dim_product.product_name",
            "برند": "dim_product.brand",
            "دسته": "dim_product.category",
            "فروشنده": "dim_sales_rep.sales_rep_name",
            "کانال": "dim_customer.trade_channel",
            "انبار": "dim_warehouse.warehouse_name",
            "مسیر": "dim_route.route_name"
        }
        
        # ============================================================
        # ۲. نگاشت Intent به جدول
        # ============================================================
        self.table_map = {
            "sales": "fact_sales",
            "profit": "fact_sales",
            "customer": "dim_customer",
            "product": "dim_product",
            "visit": "fact_visits",
            "inventory": "fact_inventory",
            "finance": "fact_financial",
            "delivery": "fact_deliveries",
            "hr": "fact_hr"
        }
        
        # ============================================================
        # ۳. نگاشت متریک‌ها (برای تشخیص مستقیم)
        # ============================================================
        self.metric_keywords = {
            "هزینه سوخت": {"column": "fuel_cost", "agg": "SUM", "table": "fact_deliveries"},
            "زمان تحویل": {"column": "delivery_duration_min", "agg": "AVG", "table": "fact_deliveries"},
            "نرخ موفقیت": {"column": "strike_rate", "agg": "AVG", "table": "fact_visits"},
            "زمان ویزیت": {"column": "visit_duration_min", "agg": "AVG", "table": "fact_visits"},
            "موجودی": {"column": "ending_balance", "agg": "SUM", "table": "fact_inventory"},
            "سود": {"column": "gross_profit", "agg": "SUM", "table": "fact_sales"},
            "فروش": {"column": "net_amount", "agg": "SUM", "table": "fact_sales"},
            "درآمد": {"column": "net_amount", "agg": "SUM", "table": "fact_sales"},
            "حاشیه سود": {"column": "gross_margin_percentage", "agg": "AVG", "table": "fact_sales"},
            "مطالبات": {"column": "outstanding", "agg": "SUM", "table": "fact_financial"},
            "تحویل به موقع": {"column": "on_time", "agg": "AVG", "table": "fact_deliveries"},
            "عملکرد": {"column": "performance_score", "agg": "AVG", "table": "fact_hr"},
            "بهره وری": {"column": "productivity_score", "agg": "AVG", "table": "fact_hr"}
        }

    # ============================================================
    # ۴. دریافت اطلاعات متریک از سوال
    # ============================================================
    def get_metric_info(self, question: str) -> dict:
        """دریافت اطلاعات متریک از سوال با بررسی کامل کلمات کلیدی"""
        q = question.lower()
        
        # ۴.۱ بررسی مستقیم کلمات کلیدی
        for metric, info in self.metric_keywords.items():
            if metric in q:
                return {
                    "column": info["column"],
                    "aggregation": info["agg"],
                    "concept": metric,
                    "table": info["table"]
                }
        
        # ۴.۲ بررسی مترادف‌ها
        if "سوخت" in q or "fuel" in q:
            return {"column": "fuel_cost", "aggregation": "SUM", "concept": "هزینه سوخت", "table": "fact_deliveries"}
        if "تحویل" in q or "delivery" in q or "ارسال" in q:
            if "زمان" in q or "مدت" in q:
                return {"column": "delivery_duration_min", "aggregation": "AVG", "concept": "زمان تحویل", "table": "fact_deliveries"}
            if "به موقع" in q or "otd" in q:
                return {"column": "on_time", "aggregation": "AVG", "concept": "تحویل به موقع", "table": "fact_deliveries"}
        if "ویزیت" in q or "visit" in q or "بازدید" in q:
            if "موفقیت" in q or "نرخ" in q:
                return {"column": "strike_rate", "aggregation": "AVG", "concept": "نرخ موفقیت", "table": "fact_visits"}
            if "زمان" in q or "مدت" in q:
                return {"column": "visit_duration_min", "aggregation": "AVG", "concept": "زمان ویزیت", "table": "fact_visits"}
        if "موجودی" in q or "انبار" in q or "stock" in q or "inventory" in q:
            return {"column": "ending_balance", "aggregation": "SUM", "concept": "موجودی", "table": "fact_inventory"}
        if "سود" in q or "profit" in q:
            return {"column": "gross_profit", "aggregation": "SUM", "concept": "سود", "table": "fact_sales"}
        if "فروش" in q or "درآمد" in q or "revenue" in q:
            return {"column": "net_amount", "aggregation": "SUM", "concept": "فروش", "table": "fact_sales"}
        if "مطالبات" in q or "بدهی" in q or "receivables" in q:
            return {"column": "outstanding", "aggregation": "SUM", "concept": "مطالبات", "table": "fact_financial"}
        if "عملکرد" in q or "کارایی" in q or "performance" in q:
            return {"column": "performance_score", "aggregation": "AVG", "concept": "عملکرد", "table": "fact_hr"}
        
        # ۴.۳ استفاده از Semantic Layer
        concept = resolve_concept(question)
        if concept:
            data = get_semantic(concept)
            if data:
                return {
                    "column": data.get("column"),
                    "aggregation": data.get("aggregation", "SUM"),
                    "concept": concept,
                    "table": data.get("table")
                }
        
        # ۴.۴ پیش‌فرض نهایی
        return {"column": "net_amount", "aggregation": "SUM", "concept": "فروش", "table": "fact_sales"}

    # ============================================================
    # ۵. دریافت جدول اصلی بر اساس intent
    # ============================================================
    def get_intent_table(self, intent: str) -> str:
        """دریافت جدول اصلی بر اساس intent"""
        if intent in self.table_map:
            return self.table_map[intent]
        return "fact_sales"

    # ============================================================
    # ۶. تشخیص JOIN‌های مورد نیاز
    # ============================================================
    def get_required_joins(self, table: str, dimensions: list, filters: list) -> list:
        """تشخیص JOIN‌های مورد نیاز با مدیریت کامل"""
        joins = []
        
        for dim in dimensions:
            # ۶.۱ استان و شهر
            if dim in ["استان", "شهر"]:
                if table == "fact_sales":
                    joins.append("JOIN dim_customer ON fact_sales.customer_id = dim_customer.customer_id")
                    joins.append("JOIN dim_geography ON dim_customer.region_id = dim_geography.geo_id")
                elif table == "fact_visits":
                    joins.append("JOIN dim_sales_rep ON fact_visits.sales_rep_id = dim_sales_rep.sales_rep_id")
                    joins.append("JOIN dim_geography ON dim_sales_rep.region_id = dim_geography.geo_id")
                elif table == "fact_inventory":
                    joins.append("JOIN dim_warehouse ON fact_inventory.warehouse_id = dim_warehouse.warehouse_id")
                    joins.append("JOIN dim_geography ON dim_warehouse.region_id = dim_geography.geo_id")
            
            # ۶.۲ محصول، برند و دسته
            if dim in ["محصول", "برند", "دسته"]:
                if table == "fact_sales":
                    joins.append("JOIN dim_product ON fact_sales.product_id = dim_product.product_id")
                elif table == "fact_inventory":
                    joins.append("JOIN dim_product ON fact_inventory.product_id = dim_product.product_id")
            
            # ۶.۳ فروشنده
            if dim == "فروشنده":
                if table == "fact_sales":
                    joins.append("JOIN dim_sales_rep ON fact_sales.sales_rep_id = dim_sales_rep.sales_rep_id")
                elif table == "fact_visits":
                    joins.append("JOIN dim_sales_rep ON fact_visits.sales_rep_id = dim_sales_rep.sales_rep_id")
                elif table == "fact_hr":
                    joins.append("JOIN dim_sales_rep ON fact_hr.sales_rep_id = dim_sales_rep.sales_rep_id")
            
            # ۶.۴ انبار
            if dim == "انبار" and table == "fact_inventory":
                joins.append("JOIN dim_warehouse ON fact_inventory.warehouse_id = dim_warehouse.warehouse_id")
            
            # ۶.۵ مسیر
            if dim == "مسیر" and table == "fact_deliveries":
                joins.append("JOIN dim_route ON fact_deliveries.route_id = dim_route.route_id")
            
            # ۶.۶ کانال
            if dim == "کانال":
                if table == "fact_sales":
                    joins.append("JOIN dim_customer ON fact_sales.customer_id = dim_customer.customer_id")
        
        # حذف JOIN‌های تکراری
        seen = set()
        unique_joins = []
        for j in joins:
            if j not in seen:
                seen.add(j)
                unique_joins.append(j)
        
        return unique_joins

    # ============================================================
    # ۷. دریافت فیلتر زمان
    # ============================================================
    def get_time_filter(self, time: str) -> str:
        """دریافت فیلتر زمان بر اساس کلید زمان"""
        time_map = {
            "today": "date_id = date('now')",
            "yesterday": "date_id = date('now', '-1 day')",
            "last_week": "date_id >= date('now', '-7 days')",
            "this_month": "strftime('%Y-%m', date_id) = strftime('%Y-%m', date('now'))",
            "last_month": "strftime('%Y-%m', date_id) = strftime('%Y-%m', date('now', '-1 month'))",
            "last_3_months": "date_id >= date('now', '-3 months')",
            "last_6_months": "date_id >= date('now', '-6 months')",
            "this_year": "strftime('%Y', date_id) = strftime('%Y', date('now'))",
            "last_year": "strftime('%Y', date_id) = strftime('%Y', date('now', '-1 year'))",
            "ytd": "date_id >= date('now', 'start of year')"
        }
        return time_map.get(time, "")

    # ============================================================
    # ۸. ساخت کوئری نهایی
    # ============================================================
    def build_sql(self, question: str, intent_result: dict) -> str:
        """ساخت کوئری نهایی بر اساس سوال و Intent Detection"""
        
        intent = intent_result.get("intent")
        dimensions = intent_result.get("dimensions", [])
        filters = intent_result.get("filters", [])
        time = intent_result.get("time")
        operator = intent_result.get("operator", "list")
        
        # ۸.۱ تشخیص جدول اصلی
        table = self.get_intent_table(intent)
        
        # ۸.۲ تشخیص متریک از سوال
        metric_info = self.get_metric_info(question)
        if metric_info.get("table"):
            table = metric_info["table"]
        
        # ۸.۳ ساخت SELECT
        dim_columns = []
        for dim in dimensions:
            if dim in self.dimension_columns:
                dim_columns.append(self.dimension_columns[dim])
        
        if dim_columns:
            select_parts = dim_columns.copy()
            if metric_info.get("column"):
                agg = metric_info["aggregation"]
                col = metric_info["column"]
                select_parts.append(f"ROUND({agg}({col}), 2) as value")
            else:
                select_parts.append("COUNT(*) as value")
            select = ", ".join(select_parts)
        else:
            if metric_info.get("column"):
                agg = metric_info["aggregation"]
                col = metric_info["column"]
                select = f"ROUND({agg}({col}), 2) as value"
            else:
                select = "COUNT(*) as value"
        
        sql = f"SELECT {select} FROM {table}"
        
        # ۸.۴ اضافه کردن JOIN‌ها
        joins = self.get_required_joins(table, dimensions, filters)
        if joins:
            sql += " " + " ".join(joins)
        
        # ۸.۵ اضافه کردن WHERE
        where_parts = []
        
        for f in filters:
            if f not in where_parts:
                where_parts.append(f)
        
        if time:
            time_filter = self.get_time_filter(time)
            if time_filter:
                where_parts.append(time_filter)
        
        if metric_info.get("rule"):
            where_parts.append(metric_info["rule"])
        
        if where_parts:
            sql += " WHERE " + " AND ".join(where_parts)
        
        # ۸.۶ اضافه کردن GROUP BY
        if dim_columns:
            sql += " GROUP BY " + ", ".join(dim_columns)
        
        # ۸.۷ اضافه کردن ORDER BY
        if dim_columns:
            if operator == "top":
                sql += " ORDER BY value DESC LIMIT 10"
            elif operator == "bottom":
                sql += " ORDER BY value ASC LIMIT 10"
            else:
                sql += " ORDER BY value DESC"
        
        # ۸.۸ برای سوالات روند، ORDER BY روی تاریخ اضافه کن
        if operator in ["trend", "growth"]:
            if "month" in sql or "date" in sql:
                if "ORDER BY" not in sql:
                    group_match = re.search(r'GROUP BY (.+?)(?: ORDER BY|$)', sql)
                    if group_match:
                        group_cols = group_match.group(1).split(',')
                        for col in group_cols:
                            col = col.strip()
                            if 'date' in col.lower() or 'month' in col.lower():
                                sql += f" ORDER BY {col} ASC"
                                break
                    else:
                        if 'month' in select:
                            sql += " ORDER BY month ASC"
                        elif 'date' in select:
                            sql += " ORDER BY date ASC"
        
        return sql


# ============================================================
# ۹. تابع برنامه‌ریزی کوئری
# ============================================================
def plan_query(question: str, intent_result: dict) -> dict:
    """برنامه‌ریزی کامل کوئری"""
    planner = QueryPlanner()
    
    sql = planner.build_sql(question, intent_result)
    
    return {
        "sql": sql,
        "table": planner.get_intent_table(intent_result.get("intent")),
        "dimensions": intent_result.get("dimensions", []),
        "filters": intent_result.get("filters", []),
        "time": intent_result.get("time"),
        "operator": intent_result.get("operator", "list"),
        "metric": planner.get_metric_info(question)
    }


# ============================================================
# ۱۰. کلاس AdvancedAnalyzer (برای فاز ۲)
# ============================================================
class AdvancedAnalyzer:
    """
    تحلیل‌گر پیشرفته داده - فاز ۲
    """
    
    def __init__(self, db_path='fmcg_distribution_complete.db'):
        self.db_path = db_path
    
    def analyze_sales_trend(self, df: pd.DataFrame) -> dict:
        """
        تحلیل روند فروش
        """
        if df is None or df.empty:
            return {'error': 'داده فروش موجود نیست'}
        
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        daily_sales = df.groupby('date')['sales'].sum()
        
        moving_avg = daily_sales.rolling(window=7).mean()
        
        return {
            'total_sales': float(df['sales'].sum()),
            'avg_daily_sales': float(df['sales'].mean()),
            'max_daily_sales': float(df['sales'].max()),
            'min_daily_sales': float(df['sales'].min()),
            'trend': 'صعودی' if daily_sales.iloc[-1] > daily_sales.iloc[0] else 'نزولی',
            'moving_average': moving_avg.tail(7).tolist()
        }
    
    def analyze_products(self, df: pd.DataFrame) -> dict:
        """
        تحلیل محصولات
        """
        if df is None or df.empty:
            return {'error': 'داده محصولات موجود نیست'}
        
        if 'product_id' not in df.columns:
            return {'error': 'ستون product_id در داده وجود ندارد'}
        
        return {
            'total_products': int(df['product_id'].nunique()),
            'top_products': df.groupby('product_id')['sales'].sum().nlargest(5).to_dict()
        }


# ============================================================
# ۱۱. تست (حذف وابستگی به intent_engine)
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🧠 تست Query Planner")
    print("=" * 60)
    
    planner = QueryPlanner()
    
    test_questions = [
        "بیشترین فروش را کدام محصول داشته؟",
        "فروش هر استان چقدر است؟",
        "موجودی هر محصول چقدر است؟",
        "روند فروش ماهانه چگونه است؟"
    ]
    
    for q in test_questions:
        print(f"\n📝 سوال: {q}")
        
        # شبیه‌سازی intent_result
        intent_result = {
            "intent": "sales",
            "dimensions": ["محصول"] if "محصول" in q else ["استان"] if "استان" in q else [],
            "filters": [],
            "time": None,
            "operator": "top" if "بیشترین" in q else "list"
        }
        
        sql = planner.build_sql(q, intent_result)
        print(f"  SQL: {sql}")