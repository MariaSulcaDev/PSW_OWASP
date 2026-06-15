"""
============================================================
 PRUEBAS FUNCIONALES AUTOMATIZADAS - SISTEMA SIGEI
============================================================

Flujo de pruebas:
  TC-001  Campos vacíos en login — el sistema no autentica
  TC-002  Login con credenciales inválidas — el sistema rechaza
  TC-003  Login exitoso — el Director accede al dashboard
  TC-004  Navegación al módulo Personal (sesión activa de TC-003)
  TC-005  Apertura del modal "Registrar docente"
  TC-006  Registro de docente y verificación de credenciales generadas
"""

import unittest
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Configuración de variables
BASE_URL = "https://lab.vallegrande.edu.pe/SIGEI/"
PERSONAL_URL = "https://lab.vallegrande.edu.pe/SIGEI/direccion/personal"
VALID_USERNAME = "mauricio.torres@sigei.gob.pe"
VALID_PASSWORD = "34534535"
INVALID_USERNAME = "invalid@sigei.gob.pe"
INVALID_PASSWORD = "invalidpassword"

_ts = str(int(time.time()))[-4:]

DOCENTE = {
  "nombres": "María Aurora",
  "apellido_paterno": "Sulca",
  "apellido_materno": "Barrera",
  "dni": f"7521{_ts}",
  "telefono": f"9{_ts}56789"[:9],
  "correo": f"m.sulca.{_ts}@gmail.com",
  "direccion": "Jr. Las Flores 456"
}

WAIT_TIMEOUT  = 20
IMPLICIT_WAIT = 5

# UTILIDADES

def crear_driver() -> webdriver.Chrome:
    opts = ChromeOptions()
    opts.add_argument("--window-size=1440,900")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.password_manager_leak_detection": False,
    })
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.implicitly_wait(IMPLICIT_WAIT)
    return driver

def evidencia(driver, nombre):
    carpeta = os.path.join(os.path.dirname(__file__), "evidencias")
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, f"{nombre}.png")
    driver.save_screenshot(ruta)
    print(f"evidencias/{nombre}.png")

def esperar(driver, by, selector, timeout=WAIT_TIMEOUT):
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((by, selector))
    )

def esperar_clic(driver, by, selector, timeout=WAIT_TIMEOUT):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, selector))
    )

def input_por_label(driver, texto_label):
    xpath = f"//label[normalize-space()='{texto_label}']/following-sibling::div//input"
    return WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.visibility_of_element_located((By.XPATH, xpath))
    )

def limpiar_sesion(driver):
    try:
        driver.execute_script("localStorage.clear(); sessionStorage.clear();")
    except Exception:
        pass
    driver.get(BASE_URL)
    time.sleep(2)

# SUITE DE PRUEBAS

class TestSIGEIPersonal(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n" + "="*62)
        print("  PRUEBAS FUNCIONALES SIGEI — Módulo: Personal / Docentes")
        print("="*62)
        print(f"  URL base  : {BASE_URL}")
        print(f"  Navegador : Google Chrome")
        print(f"  DNI prueba: {DOCENTE['dni']}")
        print("="*62)
        cls.driver = crear_driver()

    @classmethod
    def tearDownClass(cls):
        time.sleep(2)
        cls.driver.quit()
        print("\n" + "="*62)
        print("  Suite finalizada. Evidencias en ./evidencias/")
        print("="*62)

    def setUp(self):
        pass

    # ----------------------------------------------------------
    # TC-001: Campos vacíos
    # ----------------------------------------------------------
    def test_01_campos_vacios(self):
        """
        TC-001 Submit con campos vacíos.
        Esperado: el formulario de login se mantiene visible.
        """
        print("\n  [TC-001] Campos vacíos — no debe autenticar")

        limpiar_sesion(self.driver)

        esperar(self.driver, By.CSS_SELECTOR, "input[placeholder='Ingresa tu usuario']")
        evidencia(self.driver, "TC001_1_formulario_vacio")

        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)
        evidencia(self.driver, "TC001_2_resultado")

        try:
            self.driver.find_element(By.CSS_SELECTOR, "form")
            formulario_presente = True
        except NoSuchElementException:
            formulario_presente = False

        self.assertTrue(formulario_presente, "TC-001 FALLÓ: el formulario desapareció")
        print("Formulario de login sigue activo")

    # ----------------------------------------------------------
    # TC-002: Credenciales inválidas
    # ----------------------------------------------------------
    def test_02_credenciales_invalidas(self):
        """
        TC-002 Login con usuario y contraseña incorrectos.
        Esperado: el sistema rechaza y no redirige.
        """
        print("\n  [TC-002] Credenciales inválidas — debe rechazar")

        limpiar_sesion(self.driver)

        campo_user = esperar(self.driver, By.CSS_SELECTOR, "input[placeholder='Ingresa tu usuario']")
        campo_user.clear()
        campo_user.send_keys(INVALID_USERNAME)

        campo_pass = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder='Ingresa tu contraseña']")
        campo_pass.clear()
        campo_pass.send_keys(INVALID_PASSWORD)

        evidencia(self.driver, "TC002_1_datos_invalidos")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(5)
        evidencia(self.driver, "TC002_2_resultado_rechazo")

        url = self.driver.current_url
        self.assertNotIn("direccion", url.lower(), "TC-002 FALLÓ: permitió el acceso")
        print("Sistema rechazó credenciales incorrectas")

    # ----------------------------------------------------------
    # TC-003: Login exitoso  →  sesión queda activa para TC-004/05/06
    # ----------------------------------------------------------
    def test_03_login_exitoso(self):
        """
        TC-003 Login con credenciales del Director.
        Esperado: redirige al dashboard. La sesión se mantiene para los tests siguientes.
        """
        print("\n  [TC-003] Login exitoso — credenciales del Director")

        # Partir desde cero
        limpiar_sesion(self.driver)

        campo_user = esperar(self.driver, By.CSS_SELECTOR, "input[placeholder='Ingresa tu usuario']")
        campo_user.clear()
        campo_user.send_keys(VALID_USERNAME)

        campo_pass = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder='Ingresa tu contraseña']")
        campo_pass.clear()
        campo_pass.send_keys(VALID_PASSWORD)

        evidencia(self.driver, "TC003_1_credenciales_correctas")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        try:
            WebDriverWait(self.driver, 15).until(
                lambda d: d.current_url != BASE_URL and "SIGEI" in d.current_url
            )
        except TimeoutException:
            pass

        time.sleep(2)
        evidencia(self.driver, "TC003_2_dashboard_director")

        url = self.driver.current_url
        self.assertNotEqual(url, BASE_URL, "TC-003 FALLÓ: no redirigió tras login")
        print(f"Acceso concedido → {url}")

    # ----------------------------------------------------------
    # TC-004: Navegación al módulo Personal
    # ----------------------------------------------------------
    def test_04_navegacion_modulo_personal(self):
        """
        TC-004 Navegar a la sección Personal (sesión activa del Director).
        Esperado: carga 'Gestión de personal institucional'.
        """
        print("\n  [TC-004] Navegación al módulo Personal")

        self.driver.get(PERSONAL_URL)
        time.sleep(3)
        evidencia(self.driver, "TC004_modulo_personal")

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//*[contains(text(),'personal institucional') "
                    "or contains(text(),'Gestion de personal')]"
                ))
            )
            cargado = True
        except TimeoutException:
            cargado = "personal" in self.driver.page_source.lower()

        self.assertTrue(cargado, "TC-004 FALLÓ: no cargó el módulo Personal")
        print("Módulo Personal cargado")

    # ----------------------------------------------------------
    # TC-005: Abrir modal "Registrar docente"
    # ----------------------------------------------------------
    def test_05_abrir_modal_nuevo_docente(self):
        """
        TC-005 Clic en 'Nuevo docente'.
        Esperado: se abre el modal 'Registrar docente'.
        """
        print("\n  [TC-005] Abrir modal 'Registrar docente'")

        if "personal" not in self.driver.current_url:
            self.driver.get(PERSONAL_URL)
            time.sleep(3)

        btn = esperar_clic(
            self.driver, By.XPATH,
            "//button[contains(.,'Nuevo docente')]"
        )
        btn.click()
        time.sleep(1.5)
        evidencia(self.driver, "TC005_modal_registro_docente")

        try:
            WebDriverWait(self.driver, 8).until(
                EC.visibility_of_element_located((
                    By.XPATH,
                    "//*[contains(text(),'Registrar docente')]"
                ))
            )
            modal_visible = True
        except TimeoutException:
            modal_visible = False

        self.assertTrue(modal_visible, "TC-005 FALLÓ: el modal no apareció")
        print("Modal 'Registrar docente' abierto")

    # ----------------------------------------------------------
    # TC-006: Registro del docente y verificación de credenciales
    # ----------------------------------------------------------
    def test_06_registro_nuevo_docente(self):
        """
        TC-006 Completar y enviar el formulario de registro de docente.
        Esperado: docente creado y modal 'Credenciales de Acceso' visible.
        """
        print("\n  [TC-006] Registro de nuevo docente")
        print(f"    Datos: {DOCENTE['nombres']} {DOCENTE['apellido_paterno']} "
              f"| DNI: {DOCENTE['dni']} | Tel: {DOCENTE['telefono']}")

        try:
            WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located((
                    By.XPATH, "//*[contains(text(),'Registrar docente')]"
                ))
            )
        except TimeoutException:
            if "personal" not in self.driver.current_url:
                self.driver.get(PERSONAL_URL)
                time.sleep(3)
            btn = esperar_clic(self.driver, By.XPATH, "//button[contains(.,'Nuevo docente')]")
            btn.click()
            time.sleep(1.5)

        evidencia(self.driver, "TC006_1_modal_vacio")

        for label, valor in [
            ("Nombres",           DOCENTE["nombres"]),
            ("Apellido paterno",  DOCENTE["apellido_paterno"]),
            ("Apellido materno",  DOCENTE["apellido_materno"]),
        ]:
            campo = input_por_label(self.driver, label)
            campo.clear()
            campo.send_keys(valor)
            time.sleep(0.3)

        campo = input_por_label(self.driver, "Numero documento")
        campo.clear()
        campo.send_keys(DOCENTE["dni"])
        time.sleep(1.5)

        campo = input_por_label(self.driver, "Telefono")
        campo.clear()
        campo.send_keys(DOCENTE["telefono"])
        time.sleep(1.5)

        campo = input_por_label(self.driver, "Correo")
        campo.clear()
        campo.send_keys(DOCENTE["correo"])
        time.sleep(0.3)

        campo = input_por_label(self.driver, "Direccion")
        campo.clear()
        campo.send_keys(DOCENTE["direccion"])
        time.sleep(0.3)

        evidencia(self.driver, "TC006_2_formulario_completo")

        btn_guardar = esperar_clic(
            self.driver, By.XPATH,
            "//button[@type='submit' and contains(.,'Guardar docente')]"
        )
        btn_guardar.click()

        try:
            WebDriverWait(self.driver, 15).until(
                EC.visibility_of_element_located((
                    By.XPATH,
                    "//*[contains(text(),'Credenciales de Acceso') "
                    "or contains(text(),'USUARIO') "
                    "or contains(text(),'CONTRASEÑA INICIAL')]"
                ))
            )
            time.sleep(1)
            evidencia(self.driver, "TC006_3_credenciales_generadas")
            print("Docente registrado — modal de credenciales visible")
            credenciales_ok = True
        except TimeoutException:
            evidencia(self.driver, "TC006_3_resultado")
            errores = [e.text for e in self.driver.find_elements(
                By.CSS_SELECTOR, "p.text-xs.text-red-500"
            ) if e.is_displayed() and e.text]
            if errores:
                print(f"    [!] Errores en formulario: {errores}")
            credenciales_ok = False

        self.assertTrue(credenciales_ok,
                        "TC-006 FALLÓ: no apareció el modal de credenciales")


# ============================================================
# PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromTestCase(TestSIGEIPersonal)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    total   = result.testsRun
    fallos  = len(result.failures) + len(result.errors)
    pasados = total - fallos

    print("\n" + "="*62)
    print(f"  Tests ejecutados : {total}")
    print(f"  Pasaron          : {pasados}")
    print(f"  Fallaron/Errores : {fallos}")
    print(f"  Evidencias en    : ./evidencias/")
    print("="*62)

    exit(0 if result.wasSuccessful() else 1)
