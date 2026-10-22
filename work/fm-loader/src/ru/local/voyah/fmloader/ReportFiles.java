package ru.local.voyah.fmloader;
import java.io.*;
public final class ReportFiles {
 public static File resolve(File directory,String name)throws FileNotFoundException {
  if(name==null||!name.matches("Voyah-FM-report-[0-9]{8}-[0-9]{6}\\.zip"))throw new FileNotFoundException("Invalid report name");
  File file=new File(directory,name);
  try{if(!file.isFile()||!file.getCanonicalFile().getParentFile().equals(directory.getCanonicalFile()))throw new FileNotFoundException("Report unavailable");}
  catch(IOException e){throw new FileNotFoundException(e.getMessage());}
  return file;
 }
}
