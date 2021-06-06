window.onload = () => {

    $.get('/stats', (data) => {
        $("#numTrees").html(data["n_trees"]);
        $("#numSpecies").html(data["n_species"]);
    });
}

showSpecies = () => {
    $.get('/listspecies', (data) => {
        var species = data["species"];
        console.log(species);
        $('#speciesList').attr('style', 'columns:' + parseInt(species.length / 11 + 1));
        species.forEach(specie => {
            $('#speciesList').append($('<li>' + specie + '</li>'));
        });
    })
    $('#animAnchor').attr('class', 'moveWelcomeLeft');        
}