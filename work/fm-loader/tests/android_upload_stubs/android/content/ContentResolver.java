package android.content;
import java.io.*;import android.net.Uri;
public class ContentResolver {
 final Context context;ContentResolver(Context c){context=c;}
 public Uri insert(Uri uri,ContentValues v){String name=(String)v.get("_display_name");context.downloads.put(name,new ByteArrayOutputStream());Object pending=v.get("is_pending");context.downloadPending.put(name,pending==null?0:((Number)pending).intValue());return new Uri(name);}
 public OutputStream openOutputStream(Uri uri){if(context.failDownloadWrite)return new OutputStream(){public void write(int b)throws IOException{throw new IOException("Download write failed");}};return context.downloads.get(uri.value);}
 public InputStream openInputStream(Uri uri)throws FileNotFoundException{ByteArrayOutputStream out=context.downloads.get(uri.value);if(out==null)throw new FileNotFoundException();byte[] data=out.toByteArray();if(context.corruptDownloadReadback&&data.length>0)data[0]^=1;return new ByteArrayInputStream(data);}
 public int update(Uri u,ContentValues v,String where,String[] args){if(context.brokenPendingPublication&&Integer.valueOf(1).equals(context.downloadPending.get(u.value)))return 0;Object pending=v.get("is_pending");if(pending!=null)context.downloadPending.put(u.value,((Number)pending).intValue());return 1;}
 public int delete(Uri u,String where,String[] args){context.downloads.remove(u.value);context.downloadPending.remove(u.value);return 1;}
}
