<?php
include_once "header.php";
?>
<div class="container">
        <div class="page-header">
            <h1>Youtube RSS Generator <small> by kofii</small></h1>
        </div>
        <h3>For file: <a href="<?php echo $file; ?>" target="_blank"><?php echo $file; ?></a>
        </h3>
        <!-- HTML form -->
        <form action="" method="post" class="form-group">
            <div class="form-group">
                <textarea name="text" id="editor"  rows="20" class="form-control"><?php echo htmlspecialchars($text) ?></textarea>
            </div>
            <div class="form-group">
                  <input type="submit" class="btn btn-primary" value="Save"/>
            </div>
        </form>
        <button onclick="got=goToGenerated()">Generated RSS</button>
        <button onclick="got=runGenerator()">Run generator</button>


        <script>
        function goToGenerated() {
          window.location.href = '/youtube_rss/generated';
        }
        </script>
        <script>
        function runGenerator() {
            window.location.href = '/youtube_rss/run.php';
        }
        </script>

<?php
include_once "footer.php";
?>
