window.onload = () => {
    // Load stats on start
    $.get('/stats', (data) => {
        $('#numTrees').html(data["n_trees"]);
        $('#numSpecies').html(data["n_species"]);
    });

}

var jsonOutput;

// Show all species in the databank
showSpecies = () => {
    $.get('/listspecies', data => {
        var species = data["species"];
        console.log(species);
        $('#speciesList').attr('style', 'columns:' + parseInt(species.length / 11 + 1));
        species.forEach(specie => {
            $('#speciesList').append($('<li>' + specie + '</li>'));
        });
    })
    $('#animAnchor').attr('class', 'moveWelcomeLeft');        
}

// Get tree item by index
getItem = () => {
    var idx = $("#idx").val();
    if (idx != ''){
        $.get("/getitem?index=" + idx, data => {
            var jsonStr = data['item'];
            jsonOutput = jsonStr;
            var jsonObj = JSON.parse(jsonStr);
            // External widget to enbale advanced json viewing.
            $('#jsonViewerTarget').jsonViewer(jsonObj, {rootCollapsable: false});
        });
        $('#jsonSnippetContainer').show();
        $('html,body').animate({
            scrollTop: $('#jsonViewerTarget').offset().top},
            'slow');
        }
}

// Trigger search when key enter is pressed in the search input bar
$('#idx').keydown(e => {
    if (e.which == 13) {
        getItem();
    }
});
$('#property').keydown(e => {
    if (e.which == 13) {
        searchDB();
    }
});
$('#value').keydown(e => {
    if (e.which == 13) {
        searchDB();
    }
});

// Save the search result to file
saveContent = (fileContents, fileName) => {
    var link = document.createElement('a');
    link.download = fileName;
    link.href = 'data:,' + fileContents;
    link.click();
}
saveJsonOutput = () => {
    saveContent(jsonOutput, "out.json");
}

// Slide back to welcome
slideBack = () => {
    $('#animAnchor').attr('class', 'moveWelcomeBack'); 
}