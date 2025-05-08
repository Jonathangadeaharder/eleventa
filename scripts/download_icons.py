import os
import requests
import shutil
from pathlib import Path

# Ensure the icons directory exists
icons_dir = Path("ui/resources/icons")
os.makedirs(icons_dir, exist_ok=True)

# Dictionary mapping icon filenames to URLs from Material Design Icons (GitHub-hosted PNGs)
# These are freely available under Apache License 2.0
ICONS = {
    # Toolbar icons
    "sales.png": "https://raw.githubusercontent.com/google/material-design-icons/master/png/action/shopping_cart_checkout/materialicons/24dp/2x/baseline_shopping_cart_checkout_black_24dp.png",
    "products.png": "https://raw.githubusercontent.com/google/material-design-icons/master/png/action/shopping_bag/materialicons/24dp/2x/baseline_shopping_bag_black_24dp.png",
    "inventory.png": "https://raw.githubusercontent.com/google/material-design-icons/master/png/content/inventory_2/materialicons/24dp/2x/baseline_inventory_2_black_24dp.png",
    "customers.png": "https://raw.githubusercontent.com/google/material-design-icons/master/png/social/people/materialicons/24dp/2x/baseline_people_black_24dp.png",
    "purchases.png": "https://raw.githubusercontent.com/google/material-design-icons/master/png/action/shopping_cart/materialicons/24dp/2x/baseline_shopping_cart_black_24dp.png",
    "invoices.png": "https://raw.githubusercontent.com/google/material-design-icons/master/png/action/receipt/materialicons/24dp/2x/baseline_receipt_black_24dp.png",
    "corte.png": "https://raw.githubusercontent.com/google/material-design-icons/master/png/editor/pie_chart/materialicons/24dp/2x/baseline_pie_chart_black_24dp.png",
    "reports.png": "https://raw.githubusercontent.com/google/material-design-icons/master/png/action/assessment/materialicons/24dp/2x/baseline_assessment_black_24dp.png",
    "config.png": "https://raw.githubusercontent.com/google/material-design-icons/master/png/action/settings/materialicons/24dp/2x/baseline_settings_black_24dp.png",
    "suppliers.png": "https://raw.githubusercontent.com/google/material-design-icons/master/png/maps/local_shipping/materialicons/24dp/2x/baseline_local_shipping_black_24dp.png",
    "cash_drawer.png": "https://raw.githubusercontent.com/google/material-design-icons/master/png/hardware/point_of_sale/materialicons/24dp/2x/baseline_point_of_sale_black_24dp.png",
    
    # Button icons
    "new.png": "https://raw.githubusercontent.com/google/material-design-icons/master/png/content/add/materialicons/24dp/2x/baseline_add_black_24dp.png",
    "edit.png": "https://raw.githubusercontent.com/google/material-design-icons/master/png/image/edit/materialicons/24dp/2x/baseline_edit_black_24dp.png",
    "delete.png": "https://raw.githubusercontent.com/google/material-design-icons/master/png/action/delete/materialicons/24dp/2x/baseline_delete_black_24dp.png",
    "departments.png": "https://raw.githubusercontent.com/google/material-design-icons/master/png/content/inbox/materialicons/24dp/2x/baseline_inbox_black_24dp.png", 
    "search.png": "https://raw.githubusercontent.com/google/material-design-icons/master/png/action/search/materialicons/24dp/2x/baseline_search_black_24dp.png",
    "print.png": "https://raw.githubusercontent.com/google/material-design-icons/master/png/action/print/materialicons/24dp/2x/baseline_print_black_24dp.png",
    "cancel.png": "https://raw.githubusercontent.com/google/material-design-icons/master/png/navigation/cancel/materialicons/24dp/2x/baseline_cancel_black_24dp.png",
    "save.png": "https://raw.githubusercontent.com/google/material-design-icons/master/png/content/save/materialicons/24dp/2x/baseline_save_black_24dp.png",
}

def download_icon(filename, url):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(icons_dir / filename, 'wb') as f:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, f)
            print(f"Downloaded: {filename}")
            return True
        else:
            print(f"Failed to download {filename}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        return False

# Download all icons
success_count = 0
for filename, url in ICONS.items():
    if download_icon(filename, url):
        success_count += 1

print(f"Downloaded {success_count}/{len(ICONS)} icons successfully.") 