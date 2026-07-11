# semantic_layer.py
# ============================================================
# لایه معنایی (Semantic Layer) - مفاهیم کسب‌وکار
# ============================================================

import re
import pandas as pd

SEMANTIC_LAYER = {
    # ============================================================
    # ۱. مفاهیم فروش (Sales Concepts)
    # ============================================================
    "فروش": {
        "table": "fact_sales",
        "column": "net_amount",
        "synonyms": ["درآمد", "فروش خالص", "revenue", "net sales", "turnover"],
        "formula": "SUM({column})",
        "description": "مبلغ خالص فروش پس از اعمال تخفیف‌ها"
    },
    "سود": {
        "table": "fact_sales",
        "column": "gross_profit",
        "synonyms": ["سود ناخالص", "profit", "gross margin"],
        "formula": "SUM({column})",
        "description": "سود ناخالص = فروش - بهای تمام‌شده"
    },
    "حاشیه سود": {
        "table": "fact_sales",
        "column": "gross_margin_percentage",
        "synonyms": ["درصد سود", "margin", "profit margin"],
        "formula": "AVG({column})",
        "description": "درصد سود ناخالص به فروش"
    },
    "تعداد فروش": {
        "table": "fact_sales",
        "column": "quantity",
        "synonyms": ["حجم فروش", "تعداد", "quantity", "volume"],
        "formula": "SUM({column})",
        "description": "تعداد واحدهای فروخته‌شده"
    },
    
    # ============================================================
    # ۲. مفاهیم مشتریان (Customer Concepts)
    # ============================================================
    "مشتری": {
        "table": "dim_customer",
        "columns": ["customer_id", "customer_name"],
        "synonyms": ["خریدار", "client", "buyer"],
        "description": "اطلاعات مشتریان"
    },
    "مشتری فعال": {
        "table": "fact_sales",
        "rule": "date_id >= date('now', '-90 days')",
        "synonyms": ["active customer", "مشتریان فعال"],
        "description": "مشتریانی که در ۹۰ روز اخیر خرید داشته‌اند"
    },
    "مشتری VIP": {
        "table": "fact_sales",
        "rule": "net_amount >= 50000000",
        "synonyms": ["مشتری ویژه", "vip customer"],
        "description": "مشتریانی که بیش از ۵۰ میلیون تومان خرید داشته‌اند"
    },
    
    # ============================================================
    # ۳. مفاهیم محصولات (Product Concepts)
    # ============================================================
    "محصول": {
        "table": "dim_product",
        "columns": ["product_id", "product_name"],
        "synonyms": ["کالا", "sku", "item", "goods"],
        "description": "اطلاعات محصولات"
    },
    "دسته محصول": {
        "table": "dim_product",
        "column": "category",
        "synonyms": ["گروه کالا", "product category", "category"],
        "description": "دسته‌بندی محصولات"
    },
    "برند": {
        "table": "dim_product",
        "column": "brand",
        "synonyms": ["brand", "نام تجاری"],
        "description": "برند محصول"
    },
    
    # ============================================================
    # ۴. مفاهیم جغرافیایی (Geography Concepts)
    # ============================================================
    "استان": {
        "table": "dim_geography",
        "column": "province_name",
        "synonyms": ["province", "استان‌ها"],
        "description": "نام استان"
    },
    "شهر": {
        "table": "dim_geography",
        "column": "city_name",
        "synonyms": ["city", "شهرها"],
        "description": "نام شهر"
    },
    
    # ============================================================
    # ۵. مفاهیم ویزیت (Visit Concepts)
    # ============================================================
    "ویزیت": {
        "table": "fact_visits",
        "synonyms": ["بازدید", "مراجعه", "visit", "call"],
        "description": "ثبت ویزیت‌های فروشندگان"
    },
    "نرخ موفقیت": {
        "table": "fact_visits",
        "column": "strike_rate",
        "synonyms": ["موفقیت", "success rate", "hit rate"],
        "formula": "AVG({column})",
        "description": "نرخ تبدیل ویزیت به فروش"
    },
    "زمان ویزیت": {
        "table": "fact_visits",
        "column": "visit_duration_min",
        "synonyms": ["مدت ویزیت", "طول بازدید", "visit duration"],
        "formula": "AVG({column})",
        "description": "میانگین مدت زمان هر ویزیت"
    },
    
    # ============================================================
    # ۶. مفاهیم موجودی (Inventory Concepts)
    # ============================================================
    "موجودی": {
        "table": "fact_inventory",
        "column": "ending_balance",
        "synonyms": ["انبار", "stock", "warehouse", "inventory"],
        "formula": "SUM({column})",
        "description": "موجودی فعلی کالا"
    },
    "نقطه سفارش": {
        "table": "fact_inventory",
        "column": "reorder_point",
        "synonyms": ["reorder", "نقطه بازسفارش"],
        "description": "سطح موجودی که در آن باید سفارش جدید ثبت شود"
    },
    
    # ============================================================
    # ۷. مفاهیم مالی (Financial Concepts)
    # ============================================================
    "مطالبات": {
        "table": "fact_financial",
        "column": "outstanding",
        "synonyms": ["بدهی", "receivables", "debt"],
        "formula": "SUM({column})",
        "description": "مبلغ مطالبات از مشتریان"
    },
    "DSO": {
        "table": "fact_financial",
        "column": "dso",
        "synonyms": ["روزهای وصول", "days sales outstanding"],
        "formula": "AVG({column})",
        "description": "میانگین روزهای وصول مطالبات"
    },
    
    # ============================================================
    # ۸. مفاهیم توزیع (Distribution Concepts)
    # ============================================================
    "تحویل": {
        "table": "fact_deliveries",
        "synonyms": ["ارسال", "delivery", "shipment"],
        "description": "اطلاعات تحویل و ارسال کالا"
    },
    "تحویل به‌موقع": {
        "table": "fact_deliveries",
        "column": "on_time",
        "synonyms": ["on-time delivery", "OTD"],
        "formula": "AVG({column}) * 100",
        "description": "درصد تحویل‌های به‌موقع"
    },
    
    # ============================================================
    # ۹. مفاهیم منابع انسانی (HR Concepts)
    # ============================================================
    "عملکرد": {
        "table": "fact_hr",
        "column": "performance_score",
        "synonyms": ["کارایی", "performance", "efficiency"],
        "formula": "AVG({column})",
        "description": "امتیاز عملکرد کارکنان"
    },
    "فروشنده": {
        "table": "dim_sales_rep",
        "columns": ["sales_rep_id", "sales_rep_name"],
        "synonyms": ["نماینده فروش", "sales rep", "agent"],
        "description": "اطلاعات فروشندگان"
    }
}

# ============================================================
# ۱۰. مترادف‌های ترکیبی (برای تشخیص بهتر)
# ============================================================

SYNONYM_MAP = {
    "فروش": ["فروش", "درآمد", "فروش خالص", "revenue", "net sales", "turnover"],
    "سود": ["سود", "سود ناخالص", "profit", "gross margin", "حاشیه سود"],
    "مشتری": ["مشتری", "مشتریان", "خریدار", "client", "buyer", "customer"],
    "محصول": ["محصول", "کالا", "sku", "item", "product"],
    "استان": ["استان", "province", "استان‌ها"],
    "شهر": ["شهر", "city", "شهرها"],
    "ویزیت": ["ویزیت", "بازدید", "مراجعه", "visit", "call"],
    "موجودی": ["موجودی", "انبار", "stock", "warehouse", "inventory"],
    "تحویل": ["تحویل", "ارسال", "delivery", "shipment"],
    "مطالبات": ["مطالبات", "بدهی", "receivables", "debt"],
    "عملکرد": ["عملکرد", "کارایی", "performance", "efficiency"],
    "فروشنده": ["فروشنده", "نماینده فروش", "sales rep", "agent"]
}

# ============================================================
# ۱۱. قوانین کسب‌وکار (Business Rules)
# ============================================================

BUSINESS_RULES = {
    "مشتری فعال": {
        "condition": "date_id >= date('now', '-90 days')",
        "description": "مشتریانی که در ۹۰ روز اخیر خرید داشته‌اند"
    },
    "مشتری VIP": {
        "condition": "net_amount >= 50000000",
        "description": "مشتریانی که بیش از ۵۰ میلیون تومان خرید داشته‌اند"
    },
    "مشتری پرریسک": {
        "condition": "payment_terms > 60",
        "description": "مشتریانی که شرایط پرداخت بالای ۶۰ روز دارند"
    },
    "محصول پرفروش": {
        "condition": "SUM(quantity) > 100",
        "description": "محصولاتی که بیش از ۱۰۰ عدد فروش داشته‌اند"
    },
    "محصول کم‌موجود": {
        "condition": "ending_balance < reorder_point",
        "description": "محصولاتی که موجودی آنها زیر نقطه سفارش است"
    }
}

# ============================================================
# ۱۲. توابع کمکی (دست نخورده)
# ============================================================

def get_semantic(term: str) -> dict:
    """دریافت اطلاعات معنایی یک مفهوم"""
    term = term.lower()
    for concept, data in SEMANTIC_LAYER.items():
        if concept.lower() == term:
            return data
    return None

def get_synonyms(term: str) -> list:
    """دریافت مترادف‌های یک مفهوم"""
    term = term.lower()
    for concept, synonyms in SYNONYM_MAP.items():
        if concept.lower() == term:
            return synonyms
    return []

def get_rule(rule_name: str) -> dict:
    """دریافت اطلاعات یک قانون کسب‌وکار"""
    rule_name = rule_name.lower()
    for name, data in BUSINESS_RULES.items():
        if name.lower() == rule_name:
            return data
    return None

def resolve_concept(question: str) -> str:
    """تشخیص مفهوم از سوال کاربر"""
    q = question.lower()
    
    for concept, synonyms in SYNONYM_MAP.items():
        for synonym in synonyms:
            if synonym in q:
                return concept
    
    for concept in SEMANTIC_LAYER.keys():
        if concept.lower() in q:
            return concept
    
    return None

def build_kpi_query(concept: str, dimension: str = None, filter_str: str = "") -> str:
    """ساخت کوئری برای یک مفهوم با فرمول تعریف‌شده"""
    data = get_semantic(concept)
    if not data:
        return None
    
    table = data.get("table")
    column = data.get("column")
    formula = data.get("formula", "SUM({column})")
    
    if not table:
        return None
    
    if column:
        select = formula.replace("{column}", column)
    else:
        select = f"COUNT(*) as {concept}"
    
    sql = f"SELECT {select} as {concept} FROM {table}"
    
    if "rule" in data:
        sql += f" WHERE {data['rule']}"
    
    if filter_str and "WHERE" not in sql:
        sql += f" WHERE {filter_str}"
    elif filter_str:
        sql += f" AND {filter_str}"
    
    return sql

# ============================================================
# ۱۳. کلاس SemanticLayer (بهبود یافته)
# ============================================================

class SemanticLayer:
    """
    لایه معنایی - تحلیل و تفسیر سوالات کاربر (بهبود یافته)
    """
    
    def __init__(self):
        self.concepts = SEMANTIC_LAYER
        self.synonyms = SYNONYM_MAP
        self.rules = BUSINESS_RULES
        
        # ============================================================
        # اضافات جدید برای تشخیص بهتر
        # ============================================================
        
        # کلمات کلیدی زمان
        self.time_keywords = {
            'امروز': 'today',
            'دیروز': 'yesterday',
            'ماه گذشته': 'last_month',
            'هفته گذشته': 'last_week',
            'سال گذشته': 'last_year',
            'امسال': 'this_year',
            'ماه': 'month',
            'سال': 'year'
        }
        
        # کلمات کلیدی برای تشخیص قصد (بهبود یافته)
        self.intent_keywords = {
            'sales_analysis': ['فروش', 'درآمد', 'revenue', 'فروش کل', 'میزان فروش', 'فروش خالص'],
            'inventory_check': ['موجودی', 'انبار', 'stock', 'inventory', 'ذخیره', 'کمبود'],
            'profit_analysis': ['سود', 'حاشیه سود', 'profit', 'margin', 'سودآوری'],
            'customer_analysis': ['مشتری', 'خریدار', 'customer', 'client', 'مشتریان'],
            'product_analysis': ['محصول', 'کالا', 'product', 'item', 'sku', 'محصولات'],
            'comparison': ['مقایسه', 'نسبت', 'compare', 'در مقایسه با', 'تفاوت'],
            'prediction': ['پیش‌بینی', 'آینده', 'forecast', 'predict', 'تخمین', 'برآورد'],
            'trend': ['روند', 'تغییرات', 'روند فروش', 'trend', 'growth', 'رشد']
        }
    
    def analyze(self, text: str) -> dict:
        """
        تحلیل متن و تشخیص مفاهیم (بهبود یافته)
        """
        if not text:
            return {'error': 'متن ورودی خالی است'}
        
        text_lower = text.lower()
        detected = []
        
        # ============================================================
        # ۱. تشخیص مفاهیم از SEMANTIC_LAYER
        # ============================================================
        for concept, data in self.concepts.items():
            synonyms = data.get('synonyms', [])
            if concept.lower() in text_lower:
                detected.append({
                    'concept': concept,
                    'table': data.get('table'),
                    'confidence': 0.9
                })
            else:
                for syn in synonyms:
                    if syn.lower() in text_lower:
                        detected.append({
                            'concept': concept,
                            'table': data.get('table'),
                            'confidence': 0.8
                        })
                        break
        
        # ============================================================
        # ۲. تشخیص زمان (اضافه شده)
        # ============================================================
        detected_time = None
        for word, value in self.time_keywords.items():
            if word in text_lower:
                detected_time = value
                break
        
        # ============================================================
        # ۳. تشخیص قصد (بهبود یافته)
        # ============================================================
        intent_scores = {}
        for intent, keywords in self.intent_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            if score > 0:
                intent_scores[intent] = score
        
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = min(1.0, intent_scores[best_intent] / 3)
        else:
            best_intent = 'general'
            confidence = 0.1
        
        # ============================================================
        # ۴. استخراج موجودیت‌ها (اضافه شده)
        # ============================================================
        entities = {}
        if detected_time:
            entities['time'] = detected_time
        
        # تشخیص اعداد
        numbers = re.findall(r'\d+', text)
        if numbers:
            entities['numbers'] = numbers
        
        # ============================================================
        # ۵. خروجی نهایی
        # ============================================================
        return {
            'text': text,
            'detected_concepts': detected[:5],
            'intent': best_intent,
            'confidence': confidence,
            'entities': entities,
            'intent_scores': intent_scores
        }
    
    def _detect_intent(self, text: str) -> str:
        """تشخیص قصد کلی (برای سازگاری با کدهای قدیمی)"""
        if any(w in text for w in ['فروش', 'درآمد', 'revenue']):
            return 'sales_analysis'
        if any(w in text for w in ['موجودی', 'انبار', 'stock']):
            return 'inventory_check'
        if any(w in text for w in ['مشتری', 'خریدار', 'customer']):
            return 'customer_analysis'
        if any(w in text for w in ['پیش‌بینی', 'آینده', 'forecast']):
            return 'prediction'
        if any(w in text for w in ['مقایسه', 'نسبت', 'compare']):
            return 'comparison'
        return 'general'
    
    def get_concept_info(self, concept: str) -> dict:
        """دریافت اطلاعات یک مفهوم"""
        return self.concepts.get(concept, {})
    
    def build_query(self, concept: str, filters: dict = None) -> str:
        """ساخت کوئری برای یک مفهوم"""
        data = self.get_concept_info(concept)
        if not data:
            return None
        
        table = data.get('table')
        column = data.get('column')
        formula = data.get('formula', 'SUM({column})')
        
        if not table:
            return None
        
        if column:
            select = formula.replace('{column}', column)
        else:
            select = f"COUNT(*) as {concept}"
        
        sql = f"SELECT {select} as {concept} FROM {table}"
        
        if 'rule' in data:
            sql += f" WHERE {data['rule']}"
        
        return sql

# ============================================================
# ۱۴. کلاس IntentEngine (دست نخورده)
# ============================================================

class IntentEngine:
    """
    موتور تشخیص قصد کاربر
    """
    
    def __init__(self):
        self.intent_patterns = {
            'sales_query': ['فروش', 'چقدر فروش', 'میزان فروش', 'درآمد', 'revenue'],
            'inventory_query': ['موجودی', 'انبار', 'ذخیره', 'stock', 'inventory'],
            'profit_query': ['سود', 'حاشیه سود', 'margin', 'profit'],
            'comparison_query': ['مقایسه', 'نسبت به', 'در مقایسه با', 'compare'],
            'prediction_query': ['پیش‌بینی', 'تخمین', 'آینده', 'forecast', 'predict'],
            'customer_query': ['مشتری', 'خریدار', 'مشتریان', 'customer'],
            'product_query': ['محصول', 'کالا', 'product', 'item'],
            'trend_query': ['روند', 'تغییرات', 'روند فروش', 'trend']
        }
        
        self.intent_priority = {
            'prediction_query': 5,
            'sales_query': 4,
            'profit_query': 4,
            'comparison_query': 3,
            'trend_query': 3,
            'inventory_query': 2,
            'customer_query': 2,
            'product_query': 2
        }
    
    def detect_intent(self, text: str) -> dict:
        """
        تشخیص قصد کاربر از متن
        """
        if not text:
            return {'intent': 'unknown', 'confidence': 0}
        
        text_lower = text.lower()
        scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    scores[intent] = scores.get(intent, 0) + 1
        
        if not scores:
            return {'intent': 'general', 'confidence': 0.2}
        
        best_intent = max(scores, key=lambda x: (scores[x], self.intent_priority.get(x, 0)))
        confidence = min(1.0, scores[best_intent] / 3)
        
        return {
            'intent': best_intent,
            'confidence': confidence,
            'all_scores': scores
        }
    
    def get_intent_description(self, intent: str) -> str:
        """دریافت توضیح قصد"""
        descriptions = {
            'sales_query': 'سوال درباره فروش و درآمد',
            'inventory_query': 'سوال درباره موجودی انبار',
            'profit_query': 'سوال درباره سود و حاشیه سود',
            'comparison_query': 'سوال مقایسه‌ای',
            'prediction_query': 'سوال درباره پیش‌بینی آینده',
            'customer_query': 'سوال درباره مشتریان',
            'product_query': 'سوال درباره محصولات',
            'trend_query': 'سوال درباره روند تغییرات'
        }
        return descriptions.get(intent, 'سوال عمومی')