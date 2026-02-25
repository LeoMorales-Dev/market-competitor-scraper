### IMPORTACIÓN DE LIBRERÍAS ###
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# Configuración de directorios profesional y anonimizada
user_home = os.path.expanduser("~")
descargas_directorio = os.path.join(user_home, "Downloads", "Market_Intelligence_Files")

if not os.path.exists(descargas_directorio):
    os.makedirs(descargas_directorio)

spinner_selector = (By.CLASS_NAME, "mask")

### DATOS DE CONEXIÓN PROTEGIDOS ###
# Las credenciales se leen desde el sistema para evitar subirlas a GitHub
url_login = os.getenv("PORTAL_URL", "https://portal.marginfuel.com/Home/Login")
usuario = os.getenv("PORTAL_USER", "tu_usuario_aqui")
password = os.getenv("PORTAL_PASS", "tu_password_aqui")

## PARAMETROS DE ITERACIÓN ##
location_map = {
    "Cancun Airport": "CAN",
    "Guadalajara Airport": "GDL",
    "Leon Airport": "LEO",
    "Los Cabos Airport": "SAN",
    "Merida Airport": "MER",
    "Mexico City Airport": "MEX",
    "Monterrey Airport": "MTY",
    "Puerto Vallarta Airport": "PVR",
    "Queretaro Airport": "QUE",
    "Tijuana Airport": "TIJ",
}

markets = ["Mexico", "USA"]
durations = ["1", "7"]
fechas_ddmm = datetime.now().strftime("%d%m")

### Configuración de reintentos ###
max_retries = 3
spinner_timeout = 180

### CONFIGURACIÓN DEL NAVEGADOR ###
chrome_options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": descargas_directorio,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True
}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.add_argument("--start-maximized")

### INICIALIZAR DRIVER ###
driver = None
def setup_driver():
    global driver
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)
        print("Driver inicializado correctamente.")
    except Exception as e:
        print(f"Error al inicializar el driver: {e}")
        exit()

### LOGIN Y NAVEGACIÓN ###
def login_and_navigate():
    """Inicia sesión y navega a la sección de Forward Market Pricing."""
    print("Iniciando sesión...")
    driver.get(url_login)

    usuario_field = (By.XPATH, "//input[@placeholder='User Name']")
    password_field = (By.XPATH, "//input[@placeholder='Password']")
    login_button_xpath = "//*[contains(text(),'LOGIN')]"
    home_menu_xpath = "//a[text()='Home']"
    monitor_menu_xpath = "//*[contains(text(),'Monitor')]"

    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located(usuario_field))
        driver.find_element(*usuario_field).send_keys(usuario)

        WebDriverWait(driver, 15).until(EC.presence_of_element_located(password_field))
        driver.find_element(*password_field).send_keys(password)

        driver.find_element(By.XPATH, login_button_xpath).click()

        WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.XPATH, home_menu_xpath)))
        print("Inicio de sesión exitoso.")

        monitor_link = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, monitor_menu_xpath)))
        monitor_link.click()

        market_link = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "ForwardMarketPricing")))
        market_link.click()

        WebDriverWait(driver, 30).until(EC.invisibility_of_element_located(spinner_selector))

    except Exception as e:
        print(f"Error durante el proceso de login/navegación: {e}")
        driver.quit()
        exit()

def toggle_sidebar():
    """Colapsa el menú lateral para maximizar el área de trabajo."""
    menu_toggle_xpath = "//i[contains(@class,'icon-double-angle-left')]"
    try:
        menu_toggle = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, menu_toggle_xpath)))
        menu_toggle.click()
    except TimeoutException:
        pass

def switch_to_iframe(driver):
    """Cambia el foco al iframe de contenido principal."""
    iframe_id = "PageContent"
    try:
        WebDriverWait(driver, 15).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, iframe_id)))
    except Exception as e:
        print(f"Error al cambiar al iframe: {e}")
        driver.quit()
        exit()

def recover_page():
    """Refresca la página en caso de error y recupera el foco."""
    try:
        driver.switch_to.default_content()
        driver.refresh()
        time.sleep(5)
        switch_to_iframe(driver)
        return True
    except:
        return False

def download_single_file(market, duration, location_name, location_code, attempt=1):
    """Lógica de descarga individual con sistema de reintentos."""
    monitor_button_xpath = "//button[@data-bind='click: Search']"
    csv_button_xpath = "//a[contains(@class,'buttons-csv')]"
    
    try:
        print(f"Procesando: {location_name} | Intento {attempt}")
        
        # Selección de parámetros
        Select(WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, "Market")))).select_by_visible_text(market)
        time.sleep(1)
        
        Select(WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, "Duration")))).select_by_value(duration)
        time.sleep(1)
        
        Select(WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, "Pickup")))).select_by_visible_text(location_name)
        time.sleep(1)

        # Ejecución de búsqueda
        driver.find_element(By.XPATH, monitor_button_xpath).click()
        WebDriverWait(driver, spinner_timeout).until(EC.invisibility_of_element_located(spinner_selector))
        time.sleep(3)

        # Descarga y renombrado
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, csv_button_xpath))).click()
        time.sleep(5)

        # Gestión de archivos descargados
        list_files = [os.path.join(descargas_directorio, f) for f in os.listdir(descargas_directorio)]
        files_only = [f for f in list_files if os.path.isfile(f)]
        files_only.sort(key=os.path.getmtime, reverse=True)
        
        if files_only:
            latest_file = files_only[0]
            new_filename = f"MarketData_{market}_{location_code}_{duration.zfill(2)}_{fechas_ddmm}.csv"
            os.rename(latest_file, os.path.join(descargas_directorio, new_filename))
            return True
        return False

    except Exception as e:
        if attempt < max_retries:
            if recover_page():
                return download_single_file(market, duration, location_name, location_code, attempt + 1)
        return False

def main():
    setup_driver()
    login_and_navigate()
    toggle_sidebar()
    switch_to_iframe(driver)

    for market in markets:
        for duration in durations:
            for loc_name, loc_code in location_map.items():
                download_single_file(market, duration, loc_name, loc_code)

    print("Proceso finalizado. Cerrando navegador.")
    driver.quit()

if __name__ == "__main__":
    main()
