window.onload = () => {
    // Load stats on start
    $.get('/stats', (data) => {
        $('#numTrees').html(data["n_trees"]);
        $('#numSpecies').html(data["n_species"]);
    });

}

var species, jsonOutput;

// Show all species in the databank
showSpecies = () => {
    if (typeof species == 'undefined') { // Avoid unnessesary calls on backend
        $.get('/listspecies', data => {
            species = data["species"];
            $('#speciesList').attr('style', 'columns:' + parseInt(species.length / 11 + 1));
            species.forEach(specie => {
                $('#speciesList').append($('<li>' + specie + '</li>'));
            });
        })
    }
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
            $('#jsonViewerContainer').empty();
            $('#jsonViewerContainer').html('<pre id="idSearchRes"></pre>');
            $('#idSearchRes').jsonViewer(jsonObj, {rootCollapsable: false, withLinks: false});
        });
        $('#numResContainer').hide();
        $('#treeTabs').hide();
        $('#jsonSnippetContainer').show();
        $('html,body').animate({
            scrollTop: $('#jsonSnippetContainer').offset().top},
            'slow');
        }
}

// Query trees via property and value
searchDB = () => {
    var property = $('#searchField').text().toLowerCase();
    var value = $('#fieldValue').text();
    if (property == 'canopy condition') {
        property = 'canopy_condition';
    }

    if (property != '' && value != ''){
        $.get('/trees?field=' + property + '&value=' + value, data => {
            var trees = data['query'];
            var num;
            $('#jsonViewerContainer').empty(); // Clear previous search results
            // Show number of results
            $('#numRes').html(trees.length);
            $('#numResContainer').show();
            // Show tabs if results > 1
            if (trees.length >= 3) {
                num = 3;
                $('#previewLabel').attr('style', 'display: inline;');
                $('.treeTab').removeClass('active');
            } else {
                num = trees.length;
                $('#previewLabel').hide();
                if (num == 1) {
                    $('#treeTab1').hide();
                }
                $('#treeTab2').hide();
            }
            // Show json data of maximal 3 trees
            for (let i = 0; i < num; i++) {
                // Show tabs
                $('#treeTabs').attr('style', 'display: flex;');
                $('#treeTab' + i).show();
                // Load data into html
                $('#jsonViewerContainer').append('<pre class="previewTree" id="tree-' + i + '"></pre>');
                $('#tree-' + i).jsonViewer(trees[i]);
                // Show only one code block
                if (i > 0) {
                    $('#tree-' + i).hide();
                }
            }
            $('#treeTab0').children().addClass('active');
        });
        $('#jsonSnippetContainer').show();
        $('html,body').animate({
            scrollTop: $('#jsonSnippetContainer').offset().top},
            'slow');

    } else {
        $("#results").html(""); // empty list
    }
}

// Toggle shown (active) tree data
toggleTab = e => {
    // Toggle active tabs
    $('.treeTab').removeClass('active');
    $(e).addClass('active');
    // Toggle shown data
    $('.previewTree').hide();
    $('#tree-' + (e.text - 1)).show();
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

// Trigger search when key enter is pressed in the search input bar
$('#idx').keydown(e => {
    if (e.which == 13) {
        getItem();
    }
});