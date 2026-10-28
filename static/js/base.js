
function expandir(id) {
    let opcoes = document.getElementById(id);

    if (opcoes.style.display === "none") {
        opcoes.style.display = "flex";
    } else {
        opcoes.style.display = "none";
    }
}
