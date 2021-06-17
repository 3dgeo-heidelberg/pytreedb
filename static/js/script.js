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
        $('#speciesList').attr('style', 'columns:' + parseInt(species.length / 11 + 1));
        species.forEach(specie => {
            $('#speciesList').append($('<li>' + specie + '</li>'));
        });
    })
    $('#animAnchor').attr('class', 'moveWelcomeLeft');        
}

// Get tree item by index
getItem = () => {
    var idx = $('#idx').val();
    if (idx != ''){
        $.get('/getitem?index=' + idx, data => {
            var jsonStr = data['item'];
            jsonOutput = jsonStr;
            var jsonObj = JSON.parse(jsonStr);
            // External widget to enbale advanced json viewing.
            $('#jsonViewerTarget').jsonViewer(jsonObj, {rootCollapsable: false, withLinks: false});
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

// Query trees via property and value
searchDB = () => {
    var property = $('#searchField').text().toLowerCase();
    var value = $('#fieldValue').text();
    if (property != '' && value != ''){
        $.get('/trees?field=' + property + '&value=' + value, data => {
            $('#results').html("");
            $('#numRes').html(data['query'].length);
            $('#numResContainer').show();
            data['query'].forEach((tree, id) => {
                if(id < 10) {
                    $('#results').append('<pre id="results-' + id + '"></pre>');
                    $('#results-' + id).jsonViewer(tree);
                }
            });
            $('#jsonSnippetContainer').show();
            $('html,body').animate({
                scrollTop: $('#jsonViewerTarget').offset().top},
                'slow');
        });

    } else {
        $("#results").html(""); // empty list
    }
}

// After selecting a field, the available values will be updated in the second dropdown
searchFieldSelected = e => {
    $('#searchField').html(e.text);
    $('#searchField').attr('style', 'color: #000');
    $('#fieldValue').html('Choose a value');
    $('#fieldValue').attr('style', 'color: #aaa');
    $('#availableValues').empty();
    switch (e.text) {
        case "Species":
            $.get('/listspecies', data => {
                data["species"].sort().forEach(specie => {
                    $('#availableValues').append(
                        '<li><a class="dropdown-item" onclick="fieldValueSelected(this)">' + specie + '</a></li>'
                    );
                });
            })
            break;
        case "Mode": 
            var modes = ['TLS', 'ALS', 'ULS'];
            modes.forEach(mode => {
                $('#availableValues').append(
                    '<li><a class="dropdown-item" onclick="fieldValueSelected(this)">' + mode + '</a></li>'
                );
            })
            break;
        case "Canopy Condition":
            var canopy_conditions = ['leaf-on', 'leaf-off'];
            canopy_conditions.forEach(cond => {
                $('#availableValues').append(
                    '<li><a class="dropdown-item" onclick="fieldValueSelected(this)">' + cond + '</a></li>'
                );
            })
            break;
        case "Quality":
            for (let i = 1; i <= 5; i++) {
                $('#availableValues').append(
                    '<li><a class="dropdown-item" onclick="fieldValueSelected(this)">' + i + '</a></li>'
                );
            }
            break;
        default:
            break;
    }
}

// Update dropdown text when users selects a value
fieldValueSelected = e => {
    $('#fieldValue').html(e.text);
    $('#fieldValue').attr('style', 'color: #000');
}

// Utility function: save a string to a file that will pop up for the user to download
saveContent = (fileContents, fileName) => {
    var link = document.createElement('a');
    link.download = fileName;
    link.href = 'data:,' + fileContents;
    link.click();
}
// Save jsonoutput to a json file
saveJsonOutput = () => {
    saveContent(jsonOutput, "out.json");
}

// Slide back to welcome
slideBack = () => {
    $('#animAnchor').attr('class', 'moveWelcomeBack'); 
}