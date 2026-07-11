# analytical_engine.py
# ============================================================
# فاز ۳: Analytical Engine - تحلیل‌های پیشرفته
# ============================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class AnalyticalEngine:
    """
    موتور تحلیل پیشرفته - روند، علی، سبد خرید
    """
    
    def __init__(self):
        self.db_path = 'fmcg_distribution_complete.db'
    
    def analyze(self, df):
        """
        تحلیل کامل داده‌ها
        """
        if df is None or df.empty:
            return {'error': 'داده موجود نیست'}
        
        results = {
            'trend_analysis': self._analyze_trend(df),
            'causal_analysis': self._analyze_causal(df),
            'basket_analysis': self._analyze_basket(df),
            'insights': []
        }
        
        # تولید بینش
        if results['trend_analysis']['direction'] == 'up':
            results['insights'].append("📈 روند فروش صعودی است")
        elif results['trend_analysis']['direction'] == 'down':
            results['insights'].append("📉 روند فروش نزولی است")
        else:
            results['insights'].append("➡️ روند فروش پایدار است")
        
        if results['trend_analysis']['growth'] > 10:
            results['insights'].append("🚀 رشد فروش قابل توجه است")
        elif results['trend_analysis']['growth'] < -10:
            results['insights'].append("⚠️ کاهش فروش قابل توجه است")
        
        return results
    
    def _analyze_trend(self, df):
        """
        تحلیل روند فروش
        """
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df_sorted = df.sort_values('date')
        
        # فروش ماهانه
        df['month'] = df['date'].dt.to_period('M')
        monthly = df.groupby('month')['sales'].sum()
        
        if len(monthly) >= 2:
            growth = ((monthly.iloc[-1] - monthly.iloc[0]) / monthly.iloc[0]) * 100 if monthly.iloc[0] > 0 else 0
            direction = 'up' if growth > 0 else 'down'
        else:
            growth = 0
            direction = 'stable'
        
        return {
            'direction': direction,
            'growth': float(growth) if not pd.isna(growth) else 0,
            'monthly_trend': {str(k): float(v) for k, v in monthly.to_dict().items()}
        }
    
    def _analyze_causal(self, df):
        """
        تحلیل علی - عوامل موثر بر فروش
        """
        if 'price' in df.columns and 'sales' in df.columns:
            correlation = df['price'].corr(df['sales'])
            
            if not pd.isna(correlation):
                if correlation < -0.3:
                    impact = 'negative'
                    insight = 'قیمت بالا باعث کاهش فروش شده است'
                elif correlation > 0.3:
                    impact = 'positive'
                    insight = 'قیمت بالا با فروش بالا همراه است'
                else:
                    impact = 'neutral'
                    insight = 'رابطه معناداری بین قیمت و فروش وجود ندارد'
                
                return {
                    'price_sales_correlation': float(correlation),
                    'impact': impact,
                    'insight': insight
                }
        
        return {'error': 'داده کافی برای تحلیل علی وجود ندارد'}
    
    def _analyze_basket(self, df):
        """
        تحلیل سبد خرید - محصولات پرفروش
        """
        if 'product_id' in df.columns:
            products = df.groupby('product_id')['sales'].sum()
            top_products = products.nlargest(5)
            total = products.sum()
            
            return {
                'top_products': {int(k): float(v) for k, v in top_products.to_dict().items()},
                'diversity': int(len(products)),
                'concentration': float(products.nlargest(1).iloc[0] / total * 100) if total > 0 else 0
            }
        
        return {'error': 'داده کافی برای تحلیل سبد خرید وجود ندارد'}