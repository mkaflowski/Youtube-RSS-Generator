
<?php  
$command = escapeshellcmd('export PYTHONIOENCODING=utf8');
$output = shell_exec($command);


$locale='pl_PL.UTF-8';
setlocale(LC_ALL,$locale);
putenv('LC_ALL='.$locale);

$path = new SplFileInfo(__FILE__);
$filePath = $path->getPath();
// $command = escapeshellcmd('PYTHONIOENCODING=utf-8 python '.$filePath.'/genRSS.py');
// $output = shell_exec($command);

$command = escapeshellcmd('python '.$filePath.'/getvideos.py');
$output = shell_exec($command);
echo $output;

?>