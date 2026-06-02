"""
Baita Photo Selector v0.2-alpha
Seleciona fotos tremidas, desfocadas, escuras, estouradas, com olhos fechados ou parecidas.
"""

import csv
import os
import shutil
import threading
import traceback
from dataclasses import dataclass, field

import cv2
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

try:
    import mediapipe as mp
except Exception:
    mp = None

try:
    import imagehash
except Exception:
    imagehash = None

try:
    import rawpy
except Exception:
    rawpy = None

APP_NAME = "Baita Photo Selector"
APP_VERSION = "0.2-alpha"

EXTENSOES_JPG = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
EXTENSOES_RAW = (".cr2", ".cr3", ".nef", ".arw", ".dng", ".raf", ".orf", ".rw2")
EXTENSOES_TODAS = EXTENSOES_JPG + EXTENSOES_RAW

PASTA_RUINS = "FOTOS_RUINS"
PASTA_COPIAS = "FOTOS_RUINS_COPIAS"
RELATORIO_NOME = "relatorio_baita_photo_selector_v0_2_alpha.csv"

PERFIS_PADRAO = {
    "Padrao": {"nitidez": 120.0, "motion": 18.0, "hash": 8, "olhos": 0.20, "centro": 0.65}
}


@dataclass
class ResultadoFoto:
    caminho: str
    motivos: list = field(default_factory=list)
    nitidez_central: float = 0.0
    nitidez_assunto: float = 0.0
    motion: float = 0.0
    brilho: float = 0.0
    escuros: float = 0.0
    estourados: float = 0.0
    score: int = 100
    grupo_id: str = ""
    melhor_do_grupo: bool = False
    destino: str = ""


class BaitaPhotoSelector:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1280x820")
        self.root.minsize(1080, 700)

        self.pasta = ""
        self.fotos = []
        self.resultados = []
        self.suspeitas = []
        self.grupos_parecidos = []
        self.index = 0
        self.historico = []
        self.cancelar = False
        self.img_tk = None

        self.var_incluir_raw = tk.BooleanVar(value=False)
        self.var_modo_copiar = tk.BooleanVar(value=True)
        self.var_relatorio = tk.BooleanVar(value=True)
        self.var_analise_central = tk.BooleanVar(value=True)
        self.var_status = tk.StringVar(value="Selecione uma pasta para começar.")
        self.var_motivo = tk.StringVar(value="")
        self.perfis = {nome: dados.copy() for nome, dados in PERFIS_PADRAO.items()}
        self.var_perfil = tk.StringVar(value="Padrao")
        self.criar_interface()

    def criar_interface(self):
        topo = tk.Frame(self.root)
        topo.pack(fill="x", padx=12, pady=8)
        tk.Button(topo, text="Selecionar pasta", command=self.selecionar_pasta, width=16).pack(side="left", padx=4)
        tk.Button(topo, text="Analisar", command=self.iniciar_analise, width=12).pack(side="left", padx=4)
        tk.Button(topo, text="Cancelar", command=self.cancelar_analise, width=12).pack(side="left", padx=4)
        tk.Label(topo, text="Perfil:").pack(side="left", padx=(18, 4))
        self.combo_perfil = ttk.Combobox(topo, textvariable=self.var_perfil, values=list(self.perfis.keys()), width=16, state="readonly")
        self.combo_perfil.pack(side="left")
        tk.Button(topo, text="+ Perfil", command=self.adicionar_perfil, width=9).pack(side="left", padx=(6, 2))
        tk.Button(topo, text="Editar", command=self.editar_perfil, width=8).pack(side="left", padx=2)
        tk.Button(topo, text="Remover", command=self.remover_perfil, width=9).pack(side="left", padx=2)
        tk.Checkbutton(topo, text="RAW", variable=self.var_incluir_raw).pack(side="left", padx=8)
        tk.Checkbutton(topo, text="Copiar", variable=self.var_modo_copiar).pack(side="left", padx=8)
        tk.Checkbutton(topo, text="CSV", variable=self.var_relatorio).pack(side="left", padx=8)
        tk.Checkbutton(topo, text="Centro/assunto", variable=self.var_analise_central).pack(side="left", padx=8)

        centro = tk.Frame(self.root)
        centro.pack(fill="both", expand=True, padx=12, pady=6)
        self.canvas = tk.Label(centro, bg="#202020")
        self.canvas.pack(fill="both", expand=True)

        info = tk.Frame(self.root)
        info.pack(fill="x", padx=12, pady=4)
        tk.Label(info, textvariable=self.var_status, font=("Arial", 12, "bold"), anchor="w").pack(fill="x")
        tk.Label(info, textvariable=self.var_motivo, font=("Arial", 11), anchor="w", fg="#444").pack(fill="x")
        self.progress = ttk.Progressbar(self.root, mode="determinate")
        self.progress.pack(fill="x", padx=12, pady=4)

        botoes = tk.Frame(self.root)
        botoes.pack(fill="x", padx=12, pady=10)
        tk.Button(botoes, text="Manter", command=self.manter_foto, width=16).pack(side="left", padx=4)
        tk.Button(botoes, text="Copiar/Mover para ruins", command=self.enviar_para_ruins, width=22).pack(side="left", padx=4)
        tk.Button(botoes, text="Voltar", command=self.voltar, width=12).pack(side="left", padx=4)
        tk.Button(botoes, text="Zoom 100%", command=self.zoom_100, width=14).pack(side="left", padx=4)
        tk.Button(botoes, text="Comparar parecidas", command=self.comparar_parecidas, width=20).pack(side="left", padx=4)
        tk.Button(botoes, text="Mover outras parecidas", command=self.mover_outras_parecidas, width=22).pack(side="left", padx=4)
        tk.Button(botoes, text="Desfazer tudo", command=self.desfazer_tudo, width=16).pack(side="right", padx=4)

    def perfil(self):
        return self.perfis.get(self.var_perfil.get(), self.perfis["Padrao"])

    def atualizar_combo_perfis(self):
        self.combo_perfil["values"] = list(self.perfis.keys())
        if self.var_perfil.get() not in self.perfis:
            self.var_perfil.set("Padrao")

    def adicionar_perfil(self):
        self.abrir_editor_perfil("adicionar")

    def editar_perfil(self):
        self.abrir_editor_perfil("editar")

    def remover_perfil(self):
        nome = self.var_perfil.get()
        if nome == "Padrao":
            messagebox.showwarning("Perfil", "O perfil Padrao é o perfil padrão e não pode ser removido.")
            return
        if nome in self.perfis and messagebox.askyesno("Remover perfil", f"Deseja remover o perfil '{nome}'?"):
            del self.perfis[nome]
            self.var_perfil.set("Padrao")
            self.atualizar_combo_perfis()

    def abrir_editor_perfil(self, modo):
        atual = self.var_perfil.get()
        base = self.perfis.get(atual, self.perfis["Padrao"]).copy()
        win = tk.Toplevel(self.root)
        win.title("Adicionar perfil" if modo == "adicionar" else "Editar perfil")
        win.geometry("390x370")
        win.resizable(False, False)
        tk.Label(win, text="Nome do perfil").pack(anchor="w", padx=14, pady=(12, 2))
        nome_var = tk.StringVar(value="" if modo == "adicionar" else atual)
        tk.Entry(win, textvariable=nome_var).pack(fill="x", padx=14)
        campos = {}
        labels = {
            "nitidez": "Limite de nitidez",
            "motion": "Limite de tremida/motion",
            "hash": "Sensibilidade fotos parecidas/hash",
            "olhos": "Limite olhos fechados",
            "centro": "Região central analisada, exemplo 0.65",
        }
        for chave, rotulo in labels.items():
            tk.Label(win, text=rotulo).pack(anchor="w", padx=14, pady=(8, 2))
            var = tk.StringVar(value=str(base[chave]))
            tk.Entry(win, textvariable=var).pack(fill="x", padx=14)
            campos[chave] = var

        def salvar():
            nome = nome_var.get().strip()
            if not nome:
                messagebox.showwarning("Perfil", "Informe um nome para o perfil.")
                return
            if modo == "editar" and atual == "Padrao" and nome != "Padrao":
                messagebox.showwarning("Perfil", "O perfil Padrao não pode ser renomeado.")
                return
            if modo == "adicionar" and nome in self.perfis:
                messagebox.showwarning("Perfil", "Já existe um perfil com esse nome.")
                return
            try:
                dados = {
                    "nitidez": float(campos["nitidez"].get().replace(",", ".")),
                    "motion": float(campos["motion"].get().replace(",", ".")),
                    "hash": int(float(campos["hash"].get().replace(",", "."))),
                    "olhos": float(campos["olhos"].get().replace(",", ".")),
                    "centro": float(campos["centro"].get().replace(",", ".")),
                }
                if not 0.2 <= dados["centro"] <= 1.0:
                    raise ValueError("Centro precisa estar entre 0.2 e 1.0")
            except Exception as e:
                messagebox.showerror("Perfil", f"Confira os valores.\n{e}")
                return
            if modo == "editar" and atual != nome:
                self.perfis.pop(atual, None)
            self.perfis[nome] = dados
            self.var_perfil.set(nome)
            self.atualizar_combo_perfis()
            win.destroy()
        tk.Button(win, text="Salvar perfil", command=salvar, width=18).pack(pady=14)

    def selecionar_pasta(self):
        pasta = filedialog.askdirectory()
        if not pasta:
            return
        self.pasta = pasta
        extensoes = EXTENSOES_TODAS if self.var_incluir_raw.get() else EXTENSOES_JPG
        self.fotos = [os.path.join(self.pasta, f) for f in os.listdir(self.pasta) if f.lower().endswith(extensoes)]
        self.fotos.sort()
        self.resultados, self.suspeitas, self.grupos_parecidos, self.historico = [], [], [], []
        self.index = 0
        self.progress["value"] = 0
        self.canvas.config(image="")
        self.var_status.set(f"{len(self.fotos)} fotos encontradas em: {self.pasta}")
        self.var_motivo.set("")

    def iniciar_analise(self):
        if not self.pasta or not self.fotos:
            messagebox.showwarning("Aviso", "Selecione uma pasta com fotos primeiro.")
            return
        self.cancelar = False
        threading.Thread(target=self.analisar_fotos, daemon=True).start()

    def cancelar_analise(self):
        self.cancelar = True
        self.var_status.set("Cancelando análise...")

    def carregar_imagem_cv2(self, caminho):
        ext = os.path.splitext(caminho)[1].lower()
        try:
            if ext in EXTENSOES_RAW:
                if rawpy is None:
                    return None
                with rawpy.imread(caminho) as raw:
                    rgb = raw.postprocess(use_camera_wb=True, no_auto_bright=False, output_bps=8)
                return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            return cv2.imread(caminho)
        except Exception:
            return None

    def abrir_pil(self, caminho, max_size=None):
        try:
            ext = os.path.splitext(caminho)[1].lower()
            if ext in EXTENSOES_RAW:
                img = self.carregar_imagem_cv2(caminho)
                if img is None:
                    return None
                pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            else:
                pil = Image.open(caminho).convert("RGB")
            if max_size:
                pil.thumbnail(max_size)
            return pil
        except Exception:
            return None

    def recorte_central(self, imagem):
        if not self.var_analise_central.get():
            return imagem
        p = self.perfil()["centro"]
        h, w = imagem.shape[:2]
        nw, nh = int(w * p), int(h * p)
        x1, y1 = (w - nw) // 2, (h - nh) // 2
        return imagem[y1:y1 + nh, x1:x1 + nw]

    def detectar_maior_rosto(self, imagem):
        try:
            gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
            detector = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
            faces = detector.detectMultiScale(gray, 1.1, 5, minSize=(40, 40))
            if len(faces) == 0:
                return None
            return max(faces, key=lambda r: r[2] * r[3])
        except Exception:
            return None

    def detectar_regiao_assunto(self, imagem):
        rosto = self.detectar_maior_rosto(imagem)
        if rosto is not None:
            x, y, w, h = rosto
            m = int(max(w, h) * 0.35)
            return imagem[max(0, y-m):min(imagem.shape[0], y+h+m), max(0, x-m):min(imagem.shape[1], x+w+m)]
        return self.recorte_central(imagem)

    def calcular_nitidez_cv(self, imagem):
        if imagem is None or imagem.size == 0:
            return 0.0
        gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    def calcular_motion_cv(self, imagem):
        if imagem is None or imagem.size == 0:
            return 0.0
        gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
        gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        return float(abs(abs(gx).mean() - abs(gy).mean()))

    def analisar_exposicao_cv(self, imagem):
        gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
        brilho = float(gray.mean())
        escuros = float((gray < 30).mean())
        estourados = float((gray > 245).mean())
        motivos = []
        if brilho < 55 or escuros > 0.45:
            motivos.append("foto escura")
        if brilho > 210 or estourados > 0.20:
            motivos.append("foto estourada")
        return brilho, escuros, estourados, motivos

    def calcular_ear(self, pontos, indices):
        def d(a, b):
            return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5
        p1, p2, p3, p4, p5, p6 = [pontos[i] for i in indices]
        horizontal = d(p1, p4)
        return 1 if horizontal == 0 else (d(p2, p6) + d(p3, p5)) / (2 * horizontal)

    def detectar_olhos_fechados(self, caminho):
        if mp is None:
            return False
        img = self.carregar_imagem_cv2(caminho)
        if img is None:
            return False
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        try:
            with mp.solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=8, refine_landmarks=True, min_detection_confidence=0.5) as face_mesh:
                res = face_mesh.process(rgb)
                if not res.multi_face_landmarks:
                    return False
                for face in res.multi_face_landmarks:
                    pts = face.landmark
                    esq = self.calcular_ear(pts, [33, 160, 158, 133, 153, 144])
                    direita = self.calcular_ear(pts, [362, 385, 387, 263, 373, 380])
                    if ((esq + direita) / 2) < self.perfil()["olhos"]:
                        return True
        except Exception:
            return False
        return False

    def gerar_hash_foto(self, caminho):
        if imagehash is None:
            return None
        try:
            pil = self.abrir_pil(caminho, max_size=(700, 700))
            return imagehash.phash(pil) if pil is not None else None
        except Exception:
            return None

    def detectar_fotos_parecidas(self):
        limite = self.perfil()["hash"]
        hashes = {}
        for i, foto in enumerate(self.fotos):
            if self.cancelar:
                return []
            self.atualizar_progresso(i + 1, len(self.fotos), "Criando assinatura visual")
            h = self.gerar_hash_foto(foto)
            if h is not None:
                hashes[foto] = h
        grupos, usadas, lista = [], set(), list(hashes.keys())
        for i, foto in enumerate(lista):
            if foto in usadas:
                continue
            grupo = [foto]
            usadas.add(foto)
            for outra in lista[i + 1:]:
                if outra not in usadas and hashes[foto] - hashes[outra] <= limite:
                    grupo.append(outra)
                    usadas.add(outra)
            if len(grupo) > 1:
                grupos.append(grupo)
        return grupos

    def nitidez_rapida(self, caminho):
        img = self.carregar_imagem_cv2(caminho)
        if img is None:
            return 0.0
        assunto = self.detectar_regiao_assunto(img) if self.var_analise_central.get() else img
        return self.calcular_nitidez_cv(assunto)

    def calcular_score(self, r):
        score = 100
        penalidades = {"desfocada": 35, "tremida": 25, "foto escura": 20, "foto estourada": 20, "olhos fechados": 35, "parecida - existe outra mais nítida": 30}
        for motivo, pontos in penalidades.items():
            if motivo in r.motivos:
                score -= pontos
        return max(0, min(100, score))

    def analisar_fotos(self):
        try:
            self.resultados, self.suspeitas, self.historico = [], [], []
            self.index = 0
            grupos = self.detectar_fotos_parecidas()
            self.grupos_parecidos = grupos
            grupo_lookup, melhores, repetidas = {}, {}, set()
            for gid, grupo in enumerate(grupos, start=1):
                melhor = max(grupo, key=lambda f: self.nitidez_rapida(f))
                melhores[gid] = melhor
                for foto in grupo:
                    grupo_lookup[foto] = gid
                    if foto != melhor:
                        repetidas.add(foto)
            total = len(self.fotos)
            for i, foto in enumerate(self.fotos, start=1):
                if self.cancelar:
                    self.var_status.set("Análise cancelada.")
                    return
                self.atualizar_progresso(i, total, "Analisando fotos")
                img = self.carregar_imagem_cv2(foto)
                if img is None:
                    continue
                centro = self.recorte_central(img)
                assunto = self.detectar_regiao_assunto(img) if self.var_analise_central.get() else img
                r = ResultadoFoto(caminho=foto)
                r.nitidez_central = self.calcular_nitidez_cv(centro)
                r.nitidez_assunto = self.calcular_nitidez_cv(assunto)
                r.motion = self.calcular_motion_cv(centro)
                r.brilho, r.escuros, r.estourados, motivos_exp = self.analisar_exposicao_cv(img)
                r.motivos.extend(motivos_exp)
                if max(r.nitidez_central, r.nitidez_assunto) < self.perfil()["nitidez"]:
                    r.motivos.append("desfocada")
                if r.motion < self.perfil()["motion"]:
                    r.motivos.append("tremida")
                if self.detectar_olhos_fechados(foto):
                    r.motivos.append("olhos fechados")
                gid = grupo_lookup.get(foto)
                if gid:
                    r.grupo_id = str(gid)
                    r.melhor_do_grupo = melhores[gid] == foto
                    if foto in repetidas:
                        r.motivos.append("parecida - existe outra mais nítida")
                r.score = self.calcular_score(r)
                self.resultados.append(r)
                if r.motivos:
                    self.suspeitas.append(r)
            if self.var_relatorio.get():
                self.gerar_relatorio()
            self.root.after(0, self.finalizar_analise)
        except Exception:
            erro = traceback.format_exc()
            self.root.after(0, lambda: messagebox.showerror("Erro", erro))

    def atualizar_progresso(self, atual, total, texto):
        pct = int((atual / max(total, 1)) * 100)
        self.root.after(0, lambda: self.progress.config(value=pct))
        self.root.after(0, lambda: self.var_status.set(f"{texto}: {atual}/{total} ({pct}%)"))

    def finalizar_analise(self):
        self.progress["value"] = 100
        if not self.suspeitas:
            self.var_status.set("Nenhuma foto suspeita encontrada.")
            messagebox.showinfo("Resultado", "Nenhuma foto ruim encontrada.")
            return
        self.var_status.set(f"{len(self.suspeitas)} fotos suspeitas encontradas de {len(self.fotos)} analisadas.")
        self.index = 0
        self.mostrar_foto()

    def mostrar_foto(self):
        if self.index >= len(self.suspeitas):
            self.canvas.config(image="")
            self.var_status.set("Revisão finalizada.")
            self.var_motivo.set("")
            return
        r = self.suspeitas[self.index]
        pil = self.abrir_pil(r.caminho, max_size=(1180, 560))
        if pil is None:
            self.index += 1
            self.mostrar_foto()
            return
        self.img_tk = ImageTk.PhotoImage(pil)
        self.canvas.config(image=self.img_tk)
        self.var_status.set(f"{self.index + 1}/{len(self.suspeitas)} - {os.path.basename(r.caminho)} | Qualidade: {r.score}/100")
        self.var_motivo.set(f"Motivos: {', '.join(r.motivos)} | Nitidez centro: {r.nitidez_central:.1f} | Nitidez assunto: {r.nitidez_assunto:.1f} | Motion: {r.motion:.1f} | Brilho: {r.brilho:.1f} | Grupo: {r.grupo_id or '-'}")

    def manter_foto(self):
        if self.index < len(self.suspeitas):
            self.historico.append(("manter", self.suspeitas[self.index], ""))
            self.index += 1
            self.mostrar_foto()

    def destino_unico(self, pasta, nome_arquivo):
        destino = os.path.join(pasta, nome_arquivo)
        base, ext = os.path.splitext(destino)
        n = 1
        while os.path.exists(destino):
            destino = f"{base}_{n}{ext}"
            n += 1
        return destino

    def enviar_para_ruins(self, resultado=None):
        if resultado is None:
            if self.index >= len(self.suspeitas):
                return
            resultado, avancar = self.suspeitas[self.index], True
        else:
            avancar = False
        origem = resultado.caminho
        if not os.path.exists(origem):
            return
        pasta_destino = os.path.join(self.pasta, PASTA_COPIAS if self.var_modo_copiar.get() else PASTA_RUINS)
        os.makedirs(pasta_destino, exist_ok=True)
        destino = self.destino_unico(pasta_destino, os.path.basename(origem))
        if self.var_modo_copiar.get():
            shutil.copy2(origem, destino)
            self.historico.append(("copiar", resultado, destino))
        else:
            shutil.move(origem, destino)
            resultado.destino = destino
            resultado.caminho = destino
            self.historico.append(("mover", resultado, destino))
        if avancar:
            self.index += 1
            self.mostrar_foto()

    def voltar(self):
        if not self.historico:
            return
        acao, resultado, destino = self.historico.pop()
        self.index = max(0, self.index - 1)
        if acao == "copiar" and destino and os.path.exists(destino):
            os.remove(destino)
        elif acao == "mover" and destino and os.path.exists(destino):
            original = self.destino_unico(self.pasta, os.path.basename(destino))
            shutil.move(destino, original)
            resultado.caminho = original
            resultado.destino = ""
        self.mostrar_foto()

    def desfazer_tudo(self):
        if not self.historico:
            messagebox.showinfo("Desfazer", "Nenhuma ação para desfazer.")
            return
        if not messagebox.askyesno("Confirmar", "Deseja desfazer todas as ações desta sessão?"):
            return
        while self.historico:
            acao, resultado, destino = self.historico.pop()
            try:
                if acao == "copiar" and destino and os.path.exists(destino):
                    os.remove(destino)
                elif acao == "mover" and destino and os.path.exists(destino):
                    original = self.destino_unico(self.pasta, os.path.basename(destino))
                    shutil.move(destino, original)
                    resultado.caminho = original
                    resultado.destino = ""
            except Exception:
                pass
        self.index = 0
        self.mostrar_foto()
        messagebox.showinfo("Desfeito", "Todas as ações da sessão foram desfeitas.")

    def zoom_100(self):
        if self.index >= len(self.suspeitas):
            return
        pil = self.abrir_pil(self.suspeitas[self.index].caminho)
        if pil is None:
            return
        win = tk.Toplevel(self.root)
        win.title("Zoom 100%")
        win.geometry("1100x750")
        frame = tk.Frame(win)
        frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(frame, bg="#111")
        hbar = tk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
        vbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        hbar.pack(side="bottom", fill="x")
        vbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        img = ImageTk.PhotoImage(pil)
        canvas.image = img
        canvas.create_image(0, 0, anchor="nw", image=img)
        canvas.config(scrollregion=(0, 0, pil.width, pil.height))

    def encontrar_resultado(self, caminho):
        for r in self.resultados:
            if os.path.abspath(r.caminho) == os.path.abspath(caminho):
                return r
        return None

    def comparar_parecidas(self):
        if self.index >= len(self.suspeitas):
            return
        atual = self.suspeitas[self.index]
        if not atual.grupo_id:
            messagebox.showinfo("Comparar", "Esta foto não pertence a um grupo parecido.")
            return
        gid = int(atual.grupo_id)
        grupo = self.grupos_parecidos[gid - 1]
        win = tk.Toplevel(self.root)
        win.title(f"Comparação de fotos parecidas - Grupo {gid}")
        win.geometry("1250x760")
        frame = tk.Frame(win)
        frame.pack(fill="both", expand=True)
        thumbs = []
        melhor = max(grupo, key=lambda f: self.nitidez_rapida(f))
        for i, foto in enumerate(grupo):
            box = tk.Frame(frame, bd=3, relief="solid" if foto == melhor else "groove")
            box.grid(row=i // 3, column=i % 3, padx=10, pady=10)
            pil = self.abrir_pil(foto, max_size=(360, 360))
            if pil is None:
                continue
            tkimg = ImageTk.PhotoImage(pil)
            thumbs.append(tkimg)
            tk.Label(box, image=tkimg).pack()
            texto = os.path.basename(foto)
            if foto == melhor:
                texto += "\n⭐ Mais nítida sugerida"
            texto += f"\nNitidez: {self.nitidez_rapida(foto):.1f}"
            tk.Label(box, text=texto, wraplength=340).pack(pady=4)
            tk.Button(box, text="Manter esta e copiar/mover as outras", command=lambda f=foto, g=grupo, w=win: self.manter_uma_do_grupo(f, g, w)).pack(pady=4)
        win.thumbs = thumbs

    def manter_uma_do_grupo(self, escolhida, grupo, janela):
        for foto in grupo:
            if foto == escolhida:
                continue
            r = self.encontrar_resultado(foto) or ResultadoFoto(caminho=foto, motivos=["parecida - removida manualmente"])
            self.enviar_para_ruins(r)
        janela.destroy()
        messagebox.showinfo("Grupo", "As outras fotos parecidas foram enviadas para a pasta de ruins/cópias.")

    def mover_outras_parecidas(self):
        if self.index >= len(self.suspeitas):
            return
        atual = self.suspeitas[self.index]
        if not atual.grupo_id:
            messagebox.showinfo("Grupo", "Esta foto não pertence a um grupo parecido.")
            return
        grupo = self.grupos_parecidos[int(atual.grupo_id) - 1]
        melhor = max(grupo, key=lambda f: self.nitidez_rapida(f))
        for foto in grupo:
            if foto != melhor:
                r = self.encontrar_resultado(foto) or ResultadoFoto(caminho=foto, motivos=["parecida - existe outra mais nítida"])
                self.enviar_para_ruins(r)
        messagebox.showinfo("Grupo", f"Mantida automaticamente a mais nítida:\n{os.path.basename(melhor)}")

    def gerar_relatorio(self):
        caminho_csv = os.path.join(self.pasta, RELATORIO_NOME)
        with open(caminho_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["arquivo", "score", "motivos", "nitidez_central", "nitidez_assunto", "motion", "brilho", "pixels_escuros", "pixels_estourados", "grupo", "melhor_do_grupo"])
            for r in self.resultados:
                writer.writerow([r.caminho, r.score, ", ".join(r.motivos), f"{r.nitidez_central:.2f}", f"{r.nitidez_assunto:.2f}", f"{r.motion:.2f}", f"{r.brilho:.2f}", f"{r.escuros:.4f}", f"{r.estourados:.4f}", r.grupo_id, r.melhor_do_grupo])


if __name__ == "__main__":
    root = tk.Tk()
    app = BaitaPhotoSelector(root)
    root.mainloop()
