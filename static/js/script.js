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

// Query trees via property and value
searchDB = () => {
    var property = $('#searchField').val();
    var value = $('#value').val();
    if (property != '' && value != ''){
        $.get('/trees?field=' + property + '&value=' + value, data => {
            $('#results').html("");
            $('#num_found').html(data['query'].length);
            data['query'].forEach((tree, id) => {
                if(id < 10) {
                    $('#results').append('<pre id="results-' + id + '"></pre>');
                    $('#results-' + id).jsonViewer(tree);
                }
            });
        });

    } else {
        $("#results").html(""); // empty list
    }
}

searchFieldSelected = e => {
    $('#searchField').html(e.text);
    $('#searchField').attr('style', 'color: #000');
    $('#fieldValue').html('Choose a value');
    switch (e.text) {
        case "Species":
            $.get('/listspecies', data => {
                data["species"].forEach(specie => {
                    $('#availableValues').append(
                        '<li><a class="dropdown-item" href="#" onclick="fieldValueSelected(this)">' + specie + '</a></li>'
                    );
                });
            })
            break;
        case "Mode": 
            var modes = ['TLS', 'ALS', 'ULS'];
            modes.forEach(mode => {
                $('#availableValues').append(
                    '<li><a class="dropdown-item" href="#" onclick="fieldValueSelected(this)">' + mode + '</a></li>'
                );
            })
            break;
        case "Canopy Condition":
            var canopy_conditions = ['leaf-on', 'leaf-off'];
            canopy_conditions.forEach(cond => {
                $('#availableValues').append(
                    '<li><a class="dropdown-item" href="#" onclick="fieldValueSelected(this)">' + cond + '</a></li>'
                );
            })
            break;
        case "Quality":
            for (let i = 1; i <= 5; i++) {
                $('#availableValues').append(
                    '<li><a class="dropdown-item" href="#" onclick="fieldValueSelected(this)">' + i + '</a></li>'
                );
            }
            break;
        default:
            break;
    }
}

fieldValueSelected = e => {
    $('#fieldValue').html(e.text);
    $('#fieldValue').attr('style', 'color: #000');
}

// Trigger search when key enter is pressed in the search input bar
$('#idx').keydown(e => {
    if (e.which == 13) {
        getItem();
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