#!/usr/bin/perl

my ($infile, $outfile) = @ARGV;

if($infile eq "") {
	$infile = "so2pre.txt";
	$outfile = "so2.txt";
}

# this turns hourly output into 3h-ly averages
#open IN, "so2pre.txt";
open IN, $infile;
open OUT, ">$outfile";
my $title = <IN>;
print OUT $title;
$.--;
while (<IN>)
{
  @data = split;
  my $count = $#data-7;
  foreach $i (0..$count) {$sum[$i]+=$data[$i+7]};
  if ($.%3 == 0 || eof)
  {
      for $i (0..6) {print OUT ("$data[$i] ")}
      for $i (0..$#sum){$av = sprintf("%.2f", $sum[$i]/3.0); print OUT "$av "; $sum[$i]=0}
      print OUT "\n"
  }
}
