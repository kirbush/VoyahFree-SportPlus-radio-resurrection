package ru.local.voyah.fmloader;
import android.content.*;
import android.database.*;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;
import java.io.*;
public class ReportProvider extends ContentProvider {
 public boolean onCreate(){return true;}
 File resolve(Uri uri)throws FileNotFoundException {
  if(uri.getPathSegments().size()!=1)throw new FileNotFoundException("Invalid report URI");
  return ReportFiles.resolve(getContext().getFilesDir(),uri.getLastPathSegment());
 }
 public ParcelFileDescriptor openFile(Uri uri,String mode)throws FileNotFoundException {
  if(!"r".equals(mode))throw new FileNotFoundException("Read only");
  return ParcelFileDescriptor.open(resolve(uri),ParcelFileDescriptor.MODE_READ_ONLY);
 }
 public String getType(Uri uri){return "application/zip";}
 public Cursor query(Uri uri,String[] projection,String selection,String[] args,String sort){
  try{File f=resolve(uri);MatrixCursor cursor=new MatrixCursor(new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE});cursor.addRow(new Object[]{f.getName(),f.length()});return cursor;}
  catch(FileNotFoundException e){return null;}
 }
 public Uri insert(Uri uri,ContentValues values){throw new UnsupportedOperationException("Read only");}
 public int delete(Uri uri,String s,String[] a){throw new UnsupportedOperationException("Read only");}
 public int update(Uri uri,ContentValues v,String s,String[] a){throw new UnsupportedOperationException("Read only");}
}
