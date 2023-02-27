import os
import re
import undetected_chromedriver as uc
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webdriver import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC  # noqa
import time
import unidecode
import requests
import config


class Requisicao:
    def __init__(self, pdf=True):
        self.pdf = pdf


class Disciplina:
    def __init__(self, index: int, name=None, fullPath=None, aulas=None):
        self.name = name
        self.fullPath = fullPath
        self.aulas = aulas
        self.index = index

    def __init__(self, index: int, webElement: uc.webelement.WebElement, rootPath: str):
        name = webElement.text
        name = name.split("\n")[0]
        name = cleanText(name)
        fullPath = os.path.join(rootPath, name)
        self.name = name
        self.fullPath = fullPath
        self.index = index


class Aula:
    def __init__(self, name=None, fullPath=None, url=None, pdfFile=None):
        self.name = name
        self.fullPath = fullPath
        self.url = url
        self.pdfFile = pdfFile


class Video:
    def __init__(self, name=None, fullPath=None, url=None):
        self.name = name
        self.fullPath = fullPath
        self.url = url


def cleanText(text: str) -> str:
    text = unidecode.unidecode(text)
    text = removeSpecialCharacter(text)
    if len(text) > 60:
        text = text[:61]
    while text.endswith("-") or text.endswith(" "):
        text = text[:-1]
    return text


def removeSpecialCharacter(text: str) -> str:
    text = re.sub("[^a-zA-Z0-9 ]+", "-", text)
    return text


def removeElementById(driver: uc.Chrome, id: str):
    script = f"document.querySelector('#{id}').remove()"
    try:
        driver.execute_script(script)
    except:
        return


def removeModal(driver: uc.Chrome):
    removeElementById(driver, "beamerPushModal")


def waitElementById(driver: uc.Chrome, id: str, timeout=5):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, id))
        )
    except Exception as e:
        print(e)
        print("tentou clicar mas não funcionou. Tentando novamente")


def clickElementUntilWorks(func):
    i = 0
    while True:
        try:
            t = func()
            print("tentou fazer click")
            if (t == None):
                return
        except Exception as e:
            print(i)
            print("tentou clicar mas não funcionou. Tentando novamente")
            if (i > 10):
                print(e)
                return
        i = i+1
        time.sleep(0.5)


def checkIfFileExists(path: str) -> bool:
    exists = os.path.exists(path=path)
    return exists


def downloadFile(url: str, path: str) -> bool:
    if (os.path.exists(path=path)):
        print(f'Arquivo {path} já baixado. Não vou repetir')
        return False
    print(f"baixando {path} .... aguarde !")

    headers = {"Host": "vali.qconcursos.com",
               "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.50"}

    r = requests.get(url, headers=headers)

    folder = os.path.dirname(path)
    if not (os.path.exists(folder)):
        print(folder)
        os.makedirs(folder)
    with open(path, 'wb') as f:

        bytes = f.write(r.content)
        if bytes > 0:
            print(f'Arquivo {path} baixado com sucesso !')
            return True
    return False


def checkLimitModal(driver: uc.Chrome) -> bool:
    script = "return document.querySelector(\"div[data-target='download-limit-modal.modal']\").checkVisibility()"
    return driver.execute_script(script)


def start():

    # variaveis setup:
    setupVars = config.Config()

    rootPath = setupVars.rootPath
    port = setupVars.port
    disciplinaIndex = setupVars.disciplinaIndex
    initialSite = setupVars.initialSite
    cursoUrl = setupVars.cursoUrl
    email = setupVars.email
    password = setupVars.password

    requisicao = Requisicao()
    requisicao.videos = True
    requisicao.pdf = False

    # driver = uc.Chrome()
    options = Options()
    options.add_experimental_option("safebrowsing", {"enabled": False})
    options.add_experimental_option(
        "excludeSwitches", ["disable-popup-blocking"])
    options.add_argument("--disable-popup-blocking")
    driver = uc.Chrome(chrome_options=options)

    driver.get(initialSite)
    waitElementById(driver, "login_email")
    login = driver.find_element(By.ID, "login_email")
    login.send_keys(email)
    login = driver.find_element(By.ID, "login_password")
    login.send_keys(password)

    script = "(document.querySelector(\"[name='commit']\")).click()"

    driver.execute_script(script)

    time.sleep(1)

    driver.get(cursoUrl)

    time.sleep(2)

    disciplinas = driver.find_elements(By.CLASS_NAME, "R3w9Ssde1Ept2j4mKZv8")
    # get Disciplinas
    disciplinasList = []
    for i, item in enumerate(disciplinas):
        if (i+1 in disciplinaIndex):
            disciplina = Disciplina(
                index=i, webElement=item, rootPath=rootPath)
            disciplinasList.append(disciplina)
    for disciplina in disciplinasList:
        driver.get(cursoUrl)

        waitElementById(driver, "performance-widget")
        removeModal(driver)

        script = f"document.querySelectorAll('.R3w9Ssde1Ept2j4mKZv8')[{disciplina.index}].click()"
        try:
            driver.execute_script(script)
        except Exception as e:
            print(e)
            print(
                f"não consegui clicar no link da disciplina: {disciplina.name}")
            continue
        aulas = []
        time.sleep(1)

        # get aulas
        classes = driver.find_elements(
            By.XPATH, "//div[@data-controller='tracks-show-topic']")

        for classe in classes:
            # var aula Aula
            aula = Aula()
            text = classe.text
            text = text.split("\n")[0]
            text = cleanText(text)
            element = classe.find_element(By.CLASS_NAME, "text-body")
            url = element.get_attribute("href")
            aula.name = text
            aula.url = url
            aula.fullPath = os.path.join(
                disciplina.fullPath, aula.name)
            aulas.append(aula)

        disciplina.aulas = aulas

        for aula in aulas:
            driver.get(aula.url)
            removeElementById(driver, "beamerPushModal")

            if requisicao.pdf:
                # check if file already has been downloaded before click
                aula.pdfFile = aula.fullPath + ".pdf"
                ex = checkIfFileExists(aula.pdfFile)
                print(ex)
                if (checkIfFileExists(aula.pdfFile)):
                    hasPDF = False
                    print(
                        f'arquivo {aula.pdfFile} já baixado. Não baixarei.')
                    continue

                hasPDF = True
                mainWindow = driver.current_window_handle

                # wait for download button
                try:
                    WebDriverWait(driver, 4).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//span[text()='Baixar']"))
                    )
                except:
                    hasPDF = False

                if hasPDF:
                    removeElementById(driver, "beamerPushModal")
                    print(checkLimitModal(driver))

                    clickElementUntilWorks(driver.find_element(
                        By.XPATH, "//span[text()='Baixar']").click)

                    time.sleep(1)
                    limit = checkLimitModal(driver)
                    if (limit):
                        requisicao.pdf = False

                    qtdHandles = len(driver.window_handles)
                    t = 0
                    while qtdHandles < 2:
                        qtdHandles = len(driver.window_handles)
                        time.sleep(0.5)
                        t += 1
                        if t > 9:
                            break

                    # script = "Array.from(document.querySelectorAll('span')).find(el=>el.textContent == 'Baixar').click()"

                    for wh in driver.window_handles:
                        found = False
                        if (wh != mainWindow):
                            driver.switch_to.window(wh)
                            cu = driver.current_url
                            if (driver.current_url.__contains__("vali.qconcursos")):
                                found = True
                                break

                    currentUrl = driver.current_url
                    if (found):
                        downloadFile(currentUrl, aula.pdfFile)
                        driver.close()
                    driver.switch_to.window(mainWindow)

            if requisicao.videos:
                script = "(document.querySelector(\"[data-title='Videoaulas']\")).click()"

                try:
                    WebDriverWait(driver, 4).until(
                        EC.presence_of_all_elements_located(
                            (By.CLASS_NAME, "px4iVrswCtMzKOa5ojis"))
                    )
                except Exception as e:
                    print("nao aceitou")
                    print(e)

                try:
                    driver.execute_script(script)
                except Exception as e:
                    print(e)
                    continue
                time.sleep(2)
                removeElementById(driver, "beamerPushModal")
                try:
                    WebDriverWait(driver, 4).until(
                        EC.element_to_be_clickable(
                            (By.CLASS_NAME, "wH1_DckA6q4vsEeY5Eri"))
                    )
                except Exception as e:
                    print(e)

                videosElements = driver.find_elements(
                    By.CLASS_NAME, "wH1_DckA6q4vsEeY5Eri")
                titles = driver.find_elements(
                    By.CLASS_NAME, "yAy_T7FsZTJZ8bMW62x4")
                index = 0
                for item in videosElements:
                    video = Video()
                    video.url = item.get_attribute("data-download-url")
                    text = titles[index].text
                    xx = text.split(sep="\n")
                    text = xx[0]
                    text = cleanText(text)
                    order = f"{index+1:02}"

                    if (len(text) < 5):
                        video.name = order + ".mp4"
                    else:
                        video.name = f'{order}-{text}.mp4'

                    video.fullPath = os.path.join(
                        aula.fullPath, video.name)

                    t = downloadFile(video.url, video.fullPath)
                    index = index+1


if __name__ == "__main__":

    start()
    print("Done")
    time.sleep(500)
