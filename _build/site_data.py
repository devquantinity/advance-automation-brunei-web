"""Site map of advanceautomationbrunei.com as scraped: URLs, menu labels and where each page's content comes from."""
import aabcontent as A

P = '/products-and-services'

# category slug -> menu label, picture used for the category on the live site (services1-6.jpg), menu children
CATS = {
    'custom-made': {'label': 'Custom Made', 'img': 'services1.jpg', 'children': [
        ('gaskets-and-washers', 'Gaskets and Washers'), ('rope-and-sling', 'Rope and Sling'), ('stud-bolts', 'Stud Bolts'), ('polymer-taggings', 'Polymer Taggings')]},
    'calibration-certification-services': {'label': 'Calibration & Certification', 'img': 'services2.jpg', 'children': None},
    'safety-products': {'label': 'Safety Product', 'img': 'services3.jpg', 'children': [
        ('personal-safety', 'Personal Safety'), ('safety-equipments', 'Safety Equipments')]},
    'control-and-instrument-valves': {'label': 'Control & Instrument Valves', 'img': 'services4.jpg', 'children': None},
    'capabilities': {'label': 'Capabilities', 'img': 'services5.jpg', 'children': [
        ('electrical-and-instruments', 'Electrical and Instruments'), ('temperatures-devices', 'Temperatures Devices'), ('dimension-measurement', 'Dimension Measurement')]},
    'engineering-and-services': {'label': 'Engineering And Services', 'img': 'services6.jpg', 'children': [
        ('heat-exchangers', 'Heat Exchangers'), ('engines-overhaul', 'Engines Overhaul'), ('lab-equipment-repairs', 'Lab Equipment Repairs'), ('motor-repairs', 'Motor Repairs'),
        ('pump-testing', 'Pump Testing'), ('pump-repairs', 'Pump Repairs'), ('valve-actuators-repairs', 'Valve Actuators Repairs'), ('valve-repairs', 'Valve Repairs')]},
}

# how picture captions are written on each article of the live site (see aabcontent.tidy)
CAPTIONS = {'12-advance-automation-officially-launch': 'after', '23-mou-with-ramacon-corporation': 'after',
            '14-multiple-distributorships-awards': 'before', 'calibration-certification-services': 'after'}

# The three certificate scans shown on the live home page.  The live site gives them no caption (alt = file name), so the
# captions are read off the certificates themselves: standard, the management system it covers.
CERTIFICATES = [
    {'img': 'cert/SCR-20240702-jcmj.png', 'file': 'certificate-iso-9001', 'title': 'ISO 9001:2015', 'sub': 'Quality Management System',
     'alt': 'ABS Quality Evaluations certificate of conformance ISO 9001:2015 - Advance Automation Sdn Bhd'},
    {'img': 'cert/SCR-20240702-jcrn.png', 'file': 'certificate-iso-14001', 'title': 'ISO 14001:2015', 'sub': 'Environmental Management System',
     'alt': 'ABS Quality Evaluations certificate of conformance ISO 14001:2015 - Advance Automation Sdn Bhd'},
    {'img': 'cert/SCR-20240702-jcuu.png', 'file': 'certificate-iso-45001', 'title': 'ISO 45001:2018', 'sub': 'Occupational Health and Safety Management',
     'alt': 'ABS Quality Evaluations certificate of conformance ISO 45001:2018 - Advance Automation Sdn Bhd'},
]

# Home, credentials band: plant pictures from the template library (columns one..four; the first sets the band height, 2.4:1)
CREDENTIAL_PICTURES = ['Home-three-industrial-1', 'Service-three-banner-1', 'Passwords-bg', 'Service-one-banner-2a']

NEWS_GRAPHICS = {'25-awarded-aiti-license'}      # news pictures that are a logo on white rather than a photograph

NEWS = A.news_index()                      # newest first, as listed on the live site
NEWS_DATES = A.news_dates()
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def news_date(slug, long=False):
    y, m, d = NEWS_DATES[slug].split('-')
    full = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    return f'{full[int(m) - 1]} {int(d)}, {y}' if long else f'{MONTHS[int(m) - 1]} {int(d)}, {y}'


def detail_pages():
    """(url, source page, menu label, category slug) for every product / service article."""
    out = []
    for slug, c in CATS.items():
        if c['children'] is None:
            out.append((f'{P}/{slug}', f'products-and-services/{slug}', c['label'], slug))
        else:
            for child, label in c['children']:
                out.append((f'{P}/{slug}/{child}', f'products-and-services/{slug}/{child}', label, slug))
    return out
