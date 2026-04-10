// Sélection des éléments
const openDialogButton = document.querySelector('.open-dialog-button');
const closeDialogButton = document.querySelector('#closeDialogButton');
const closeDialog = document.querySelector('#closeDialog');
const dialogOverlay = document.querySelector('#dialogOverlay');

// Fonction pour ouvrir la boîte de dialogue
openDialogButton.addEventListener('click', () => {
    dialogOverlay.style.display = 'flex'; // Afficher la boîte de dialogue
});

// Fonction pour fermer la boîte de dialogue
closeDialogButton.addEventListener('click', () => {
    dialogOverlay.style.display = 'none'; // Masquer la boîte de dialogue
});

// Fonction pour fermer la boîte de dialogue lorsque l'utilisateur clique sur la croix
closeDialog.addEventListener('click', () => {
    dialogOverlay.style.display = 'none'; // Masquer la boîte de dialogue
});
