"""
Coupon finder tool for discovering deals and promotions.
Searches and validates active promotional offers.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from .base_tool import BaseSupabaseTool


class CouponFinderTool(BaseSupabaseTool):
    """
    Tool for finding active coupons and promotional deals.
    Validates coupon validity and matches with user preferences.
    """

    name: str = "coupon_finder"
    description: str = (
        "Find active coupons and promotional deals for restaurants. "
        "Validates offers and calculates potential savings."
    )

    def _run(
        self,
        restaurant_name: Optional[str] = None,
        cuisine_type: Optional[str] = None,
        min_discount: Optional[float] = None,
        max_budget: Optional[float] = None
    ) -> str:
        """
        Find coupons matching criteria.
        
        Args:
            restaurant_name: Specific restaurant to find deals for
            cuisine_type: Type of cuisine to filter by
            min_discount: Minimum discount percentage
            max_budget: Maximum order amount for budget calculation
            
        Returns:
            Formatted coupon information with savings calculations
        """
        query_parts = []
        if restaurant_name:
            query_parts.append(restaurant_name)
        if cuisine_type:
            query_parts.append(cuisine_type)
        query_parts.append("discount promotion deal offer")
        
        query = " ".join(query_parts)
        
        coupon_results = self.search_collection(
            query=query,
            collection_name=self.settings.supabase_collection_coupons,
            limit=10
        )
        
        valid_coupons = self._filter_valid_coupons(
            coupon_results,
            restaurant_name,
            min_discount
        )
        
        if not valid_coupons:
            return f"No active coupons found for the specified criteria."
        
        output = f"🎟️ **Found {len(valid_coupons)} Active Promotions**\n\n"
        
        total_potential_savings = 0
        
        for i, coupon in enumerate(valid_coupons[:5], 1):
            metadata = coupon.get("metadata", {})
            
            discount_pct = metadata.get("discount_percentage")
            discount_amt = metadata.get("discount_amount")
            min_order = metadata.get("minimum_order")
            
            output += f"**{i}. {metadata.get('restaurant_name', 'Unknown Restaurant')}**\n"
            output += f"   📍 Code: **{metadata.get('code', 'N/A')}**\n"
            
            if discount_pct:
                output += f"   💰 Discount: {discount_pct}% off\n"
                if max_budget:
                    savings = (float(discount_pct) / 100) * max_budget
                    total_potential_savings += savings
                    output += f"   💵 Potential Savings: ${savings:.2f}\n"
            elif discount_amt:
                output += f"   💰 Discount: ${discount_amt} off\n"
                total_potential_savings += float(discount_amt)
            
            if min_order:
                output += f"   🛒 Minimum Order: ${min_order}\n"
            
            description = metadata.get("description", "")
            if description:
                output += f"   📝 Details: {description[:100]}...\n"
            
            valid_until = metadata.get("valid_until", "")
            if valid_until:
                expiry = self._parse_date(valid_until)
                if expiry:
                    days_left = (expiry - datetime.now()).days
                    if days_left > 0:
                        output += f"   ⏰ Valid for: {days_left} days\n"
                    else:
                        output += f"   ⏰ Expires: Today!\n"
            
            terms = metadata.get("terms_conditions", "")
            if terms:
                output += f"   📋 Terms: {terms[:80]}...\n"
            
            output += "\n"
        
        if max_budget and total_potential_savings > 0:
            output += f"**💰 Total Potential Savings: ${total_potential_savings:.2f}**\n"
            savings_percentage = (total_potential_savings / max_budget) * 100
            output += f"**📊 Average Discount: {savings_percentage:.1f}%**\n\n"
        
        output += "**💡 Tips for Maximum Savings:**\n"
        output += "  • Check minimum order requirements before ordering\n"
        output += "  • Some codes may be combinable - ask the restaurant\n"
        output += "  • Save codes for your next order if not needed now\n"
        output += "  • Sign up for restaurant newsletters for exclusive deals\n"
        
        return output

    def _filter_valid_coupons(
        self,
        coupon_results: List[Dict[str, Any]],
        restaurant_name: Optional[str],
        min_discount: Optional[float]
    ) -> List[Dict[str, Any]]:
        """
        Filter coupons by validity and criteria.
        
        Args:
            coupon_results: Raw coupon search results
            restaurant_name: Filter by restaurant name
            min_discount: Minimum discount percentage
            
        Returns:
            Filtered list of valid coupons
        """
        valid_coupons = []
        current_date = datetime.now()
        
        for coupon in coupon_results:
            metadata = coupon.get("metadata", {})
            
            if restaurant_name:
                coupon_restaurant = metadata.get("restaurant_name", "").lower()
                if restaurant_name.lower() not in coupon_restaurant:
                    continue
            
            if min_discount:
                discount_pct = metadata.get("discount_percentage")
                discount_amt = metadata.get("discount_amount")
                
                if discount_pct:
                    if float(discount_pct) < min_discount:
                        continue
                elif discount_amt:
                    pass
                else:
                    continue
            
            valid_from_str = metadata.get("valid_from", "")
            valid_until_str = metadata.get("valid_until", "")
            
            valid_from = self._parse_date(valid_from_str)
            valid_until = self._parse_date(valid_until_str)
            
            if valid_from and valid_from > current_date:
                continue  # Not yet valid
            
            if valid_until and valid_until < current_date:
                continue  # Expired
            
            valid_coupons.append(coupon)
        
        valid_coupons.sort(
            key=lambda x: float(x.get("metadata", {}).get("discount_percentage", 0)),
            reverse=True
        )
        
        return valid_coupons

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string to datetime object.
        
        Args:
            date_str: Date string to parse
            
        Returns:
            Datetime object or None if parsing fails
        """
        if not date_str:
            return None
        
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.split(".")[0], fmt)
            except:
                continue
        
        return None

    def find_best_deal(
        self,
        restaurant_names: List[str],
        target_budget: float
    ) -> str:
        """
        Find the best deal among multiple restaurants.
        
        Args:
            restaurant_names: List of restaurants to compare
            target_budget: Budget for comparison
            
        Returns:
            Best deal recommendation
        """
        best_deals = []
        
        for restaurant in restaurant_names:
            coupons = self._run(
                restaurant_name=restaurant,
                max_budget=target_budget
            )
            
            if "Potential Savings: $" in coupons:
                import re
                savings_match = re.search(r"Potential Savings: \$(\d+\.?\d*)", coupons)
                if savings_match:
                    savings = float(savings_match.group(1))
                    best_deals.append({
                        "restaurant": restaurant,
                        "savings": savings,
                        "details": coupons
                    })
        
        if not best_deals:
            return "No deals found for the specified restaurants."
        
        best_deals.sort(key=lambda x: x["savings"], reverse=True)
        
        output = f"🏆 **Best Deal: {best_deals[0]['restaurant']}**\n"
        output += f"Maximum Savings: ${best_deals[0]['savings']:.2f}\n\n"
        output += "Other Options:\n"
        
        for deal in best_deals[1:3]:
            output += f"  • {deal['restaurant']}: ${deal['savings']:.2f} savings\n"
        
        return output