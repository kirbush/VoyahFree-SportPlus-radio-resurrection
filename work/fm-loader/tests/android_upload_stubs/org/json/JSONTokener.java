package org.json;
/** Test-only flat JSON parser; Android supplies org.json on device. */
public class JSONTokener {
 final String text;int at;
 public JSONTokener(String s){text=s;}
 public char nextClean(){while(at<text.length()){char c=text.charAt(at++);if(!Character.isWhitespace(c))return c;}return 0;}
 String string()throws JSONException{StringBuilder out=new StringBuilder();while(at<text.length()){char c=text.charAt(at++);if(c=='"')return out.toString();if(c=='\\'){if(at>=text.length())throw new JSONException("Escape");c=text.charAt(at++);if(c=='u'){try{c=(char)Integer.parseInt(text.substring(at,at+4),16);at+=4;}catch(Exception e){throw new JSONException("Unicode");}}else if(c=='n')c='\n';else if(c=='r')c='\r';else if(c=='t')c='\t';else if(c!='"'&&c!='\\'&&c!='/')throw new JSONException("Escape");}else if(c<32)throw new JSONException("Control");out.append(c);}throw new JSONException("String");}
 Object value()throws JSONException{char c=nextClean();if(c=='"')return string();if(c=='{'){at--;return new JSONObject(this);}int start=at-1;while(at<text.length()&&",}] \r\n\t".indexOf(text.charAt(at))<0)at++;String s=text.substring(start,at);if(s.equals("true"))return true;if(s.equals("false"))return false;if(s.equals("null"))return JSONObject.NULL;try{if(s.indexOf('.')>=0||s.indexOf('e')>=0||s.indexOf('E')>=0)return Double.valueOf(s);return Long.valueOf(s);}catch(Exception e){throw new JSONException("Value");}}
}
