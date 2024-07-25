{
    # App information
    'name': 'Shopify Odoo Connector extended',
    'version': '15.0.14.4.1',
    'category': 'Sales',
    'summary': 'Our Shopify Connector helps you in integrating and managing your Shopify store with Odoo by providing the most useful features of Product and Order Synchronization. This solution is compatible with our other apps i.e. Amazon, ebay, magento, Inter Company Transfer, Shipstation.Apart from Odoo Shopify Connector, we do have other ecommerce solutions or applications such as Woocommerce connector, Magento Connector, and also we have solutions for Marketplace Integration such as Odoo Amazon Connector, Odoo eBay Connector, Odoo Walmart Connector, Odoo Bol.com Connector.Aside from ecommerce integration and ecommerce marketplace integration, we also provide solutions for various operations, such as shipping , logistics , shipping labels , and shipping carrier management with our shipping integration, known as the Shipstation connector.For the customers who are into Dropship business, we do provide EDI Integration that can help them manage their Dropshipping business with our Dropshipping integration or Dropshipper integration.It is listed as Dropshipping EDI integration and Dropshipper EDI integration.Emipro applications can be searched with different keywords like Amazon integration, Shopify integration, Woocommerce integration, Magento integration, Amazon vendor center module, Amazon seller center module, Inter company transfer, Ebay integration, Bol.com integration, inventory management, warehouse transfer module, dropship and dropshipper integration and other Odoo integration application or module',
    'license': 'OPL-1',

    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com/',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',

    # Dependencies
    'depends': ['common_connector_library','shopify_ept', 'product'],

    # Views
    'init_xml': [],
    'data': [
        'security/ir.model.access.csv',
        'view/product_template_view.xml',
        'view/product_collection_views.xml',
        # 'wizard/change_product_status_view.xml',
        'wizard/assign_collection_to_product_views.xml',
        # 'wizard/export_collection_to_shopify.xml',
        # 'view/product_log.xml',
        # 'view/product_template_view.xml',
    ],
    'demo_xml': [],
    # cloc settings
    'cloc_exclude': ["shopify/**/*",
                     "**/*.xml",
                     "wizard/**/*",
                     "models/**/*",
                     "data/**/*",
                     "report/**/*",
                     "security/**/*",
                     "static/**/*",
                     "view/**/*",
                     "wizard_views/**/*",
                     "__pycache__/**/*",
                     ],

    # Odoo Store Specific
    'images': ['static/description/Shopify_Odoo_App_v15_Video.gif'],
    "description": """
          Shopify,
          Amazon,
          Woo,
          Woocommerce,
          woo-commerce,
          Shopify Connector
          """,

    'installable': True,
    'auto_install': False,
    'live_test_url': 'https://www.emiprotechnologies.com/r/DOh'
}
