
document.querySelector('.fiche_parcelle').addEventListener('click', function () {
    let cadre = document.getElementById('cadre_frame');
    cadre.style.display='inline-block';
    let cadre2 = document.getElementById('framedis');
    cadre2.style.display='inline-block';
    let printit = document.getElementById('imprimer');
    printit.style.display= "inline-block";
    let close = document.getElementById('fermer');
    close.style.display= "inline-block";
});