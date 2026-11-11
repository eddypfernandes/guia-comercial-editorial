(function () {
  "use strict";

  function criar(tag, classe, texto) {
    var el = document.createElement(tag);
    if (classe) el.className = classe;
    if (texto) el.textContent = texto;
    return el;
  }

  function linkSeguro(valor, base) {
    try {
      var texto = String(valor || "");
      if (/^(\\/|\\.\\/|\\.\\.\\/)/.test(texto)) {
        var relativo = new URL(texto, base || document.baseURI);
        return (relativo.protocol === "https:" || relativo.protocol === "http:") ? relativo.href : "";
      }
      var url = new URL(texto);
      return url.protocol === "https:" ? url.href : "";
    } catch (_) {
      return "";
    }
  }

  function materiaValida(materia) {
    if (!materia || materia.status_editorial !== "apto_para_publicacao") return false;
    if (!materia.validade_ate) return true;
    return materia.validade_ate >= new Date().toISOString().slice(0, 10);
  }

  function criarFonte(materia) {
    var href = linkSeguro(materia.url_fonte);
    if (!href) return null;
    var link = criar("a", "gc-editorial__fonte", "Consultar fonte original");
    link.href = href;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    return link;
  }

  function criarDestaque(materia, feedUrl) {
    var destaque = criar("article", "gc-editorial__destaque");
    var areaImagem = criar("div", "gc-editorial__imagem");
    var imagemUrl = linkSeguro(materia.imagem_url, feedUrl);

    if (imagemUrl) {
      var imagem = document.createElement("img");
      imagem.src = imagemUrl;
      imagem.alt = materia.titulo || "Imagem da matéria";
      imagem.loading = "lazy";
      imagem.decoding = "async";
      imagem.addEventListener("error", function () {
        areaImagem.replaceChildren(criar("div", "gc-editorial__imagem--vazia", "Imagem indisponível"));
      }, { once: true });
      areaImagem.appendChild(imagem);
    } else {
      areaImagem.appendChild(criar("div", "gc-editorial__imagem--vazia", "Imagem não disponível"));
    }

    var texto = criar("div", "gc-editorial__texto");
    texto.appendChild(criar("span", "gc-editorial__pilar", materia.pilar || "Destaque"));
    texto.appendChild(criar("h2", "gc-editorial__titulo", materia.titulo_carrossel || materia.titulo || "Matéria editorial"));
    texto.appendChild(criar("p", "gc-editorial__resumo", materia.linha_fina_carrossel || materia.linha_fina || ""));
    var fonte = criarFonte(materia);
    if (fonte) texto.appendChild(fonte);

    destaque.append(areaImagem, texto);
    return destaque;
  }

  function criarItem(materia) {
    var item = criar("article", "gc-editorial__item");
    item.appendChild(criar("span", "gc-editorial__pilar", materia.pilar || "Editorial"));
    item.appendChild(criar("h3", "gc-editorial__item-titulo", materia.titulo_carrossel || materia.titulo || "Matéria editorial"));
    return item;
  }

  async function iniciar(raiz) {
    var feed = raiz.getAttribute("data-feed");
    if (!feed) {
      raiz.appendChild(criar("p", "gc-editorial__estado", "Informe o endereço do feed editorial em data-feed."));
      return;
    }

    try {
      var resposta = await fetch(feed, { headers: { Accept: "application/json" } });
      if (!resposta.ok) throw new Error("Feed indisponível.");
      var dados = await resposta.json();
      var feedUrl = new URL(feed, document.baseURI).href;
      var materias = Array.isArray(dados.materias) ? dados.materias.filter(materiaValida) : [];

      raiz.replaceChildren();
      if (!materias.length) {
        raiz.appendChild(criar("p", "gc-editorial__estado", "Nenhuma matéria editorial disponível no momento."));
        return;
      }

      raiz.appendChild(criarDestaque(materias[0], feedUrl));
      if (materias.length > 1) {
        var lista = criar("div", "gc-editorial__lista");
        materias.slice(1, 5).forEach(function (materia) {
          lista.appendChild(criarItem(materia));
        });
        raiz.appendChild(lista);
      }
      raiz.appendChild(criar("p", "gc-editorial__estado", "Conteúdo atualizado automaticamente pelo feed editorial."));
    } catch (_) {
      raiz.replaceChildren(criar("p", "gc-editorial__estado", "Não foi possível carregar o conteúdo editorial."));
    }
  }

  document.querySelectorAll("[data-gc-editorial]").forEach(iniciar);
})();
