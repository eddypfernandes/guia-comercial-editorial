(function () {
  const root = document.querySelector("[data-preview-editorial]");
  if (!root) return;
  const feed = root.dataset.feed;
  fetch(feed, { cache: "no-store" })
    .then(r => { if (!r.ok) throw new Error("Feed indisponível"); return r.json(); })
    .then(data => {
      const items = Array.isArray(data.materias) ? data.materias : [];
      root.innerHTML = "";
      const status = document.createElement("p");
      status.className = "preview-status";
      status.textContent = items.length + " matérias carregadas do feed • " + (data.gerado_em || "");
      root.append(status);
      items.forEach((m, i) => {
        const card = document.createElement("article");
        card.className = "preview-card" + (i === 0 ? " preview-feature" : "");
        if (m.imagem_url) {
          const img = document.createElement("img");
          img.src = m.imagem_url;
          img.alt = m.titulo || "";
          img.loading = "lazy";
          img.onerror = () => { img.replaceWith(Object.assign(document.createElement("div"), {className:"preview-noimg",textContent:"Imagem indisponível"})); };
          card.append(img);
        } else {
          const no = document.createElement("div"); no.className="preview-noimg"; no.textContent="Sem imagem"; card.append(no);
        }
        const body = document.createElement("div"); body.className="preview-body";
        const tag = document.createElement("small"); tag.textContent=(m.pilar||"Editorial").toUpperCase(); body.append(tag);
        const title = document.createElement(i===0?"h2":"h3"); title.textContent=m.titulo_carrossel||m.titulo||"Matéria"; body.append(title);
        const summary=document.createElement("p"); summary.textContent=m.linha_fina_carrossel||m.linha_fina||""; body.append(summary);
        const source=document.createElement("a"); source.href=m.url_fonte||"#"; source.target="_blank"; source.rel="noopener"; source.textContent="Ler fonte: "+(m.fonte_publicadora||"origem"); body.append(source);
        if(m.imagem_credito || m.imagem_licenca) { const credit=document.createElement("p"); credit.className="preview-credit"; credit.textContent="Imagem: "+(m.imagem_credito||"crédito não informado")+" • "+(m.imagem_licenca||"licença não informada"); body.append(credit); }
        card.append(body); root.append(card);
      });
    })
    .catch(err => { root.textContent="Falha ao carregar feed: "+err.message; });
})();