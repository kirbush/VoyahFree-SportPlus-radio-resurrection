package android.content;
import java.io.*;import android.net.Uri;
public class ContentResolver {
 final Context context;ContentResolver(Context c){context=c;}
 public Uri insert(Uri uri,ContentValues v){String name=(String)v.get("display_name");context.downloads.put(name,new ByteArrayOutputStream());return new Uri(name);}
 public OutputStream openOutputStream(Uri uri){return context.downloads.get(uri.value);}
 public int update(Uri u,ContentValues v,String where,String[] args){return 1;}
 public int delete(Uri u,String where,String[] args){context.downloads.remove(u.value);return 1;}
}
