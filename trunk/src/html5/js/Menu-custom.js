			function addWindowListItem(wid, title)
			{
				var li = document.createElement("li");
				li.className="windowlist-li";
				li.id = "windowlistitem"+wid;
				
				var a = document.createElement("a");
				
				a.id = "windowlistitemlink"+wid;
				
				a.onmouseover=function(){client._window_set_focus(client.id_to_window[wid])};
				a.onclick=function(){
					if(jQuery(client.id_to_window[wid].div).is(":hidden")){
						jQuery(client.id_to_window[wid].div).show();
					}
					this.parentElement.parentElement.className="-hide";
				};
				
				var divLeft = document.createElement("div");
				divLeft.id="windowlistdivleft"+wid;
				divLeft.className="menu-divleft";
				var img = new Image();
				img.id = "windowlistitemicon"+wid;
				img.src="/favicon.png";
				img.className="menu-content-left";
				divLeft.appendChild(img);
				
				var titleDiv = document.createElement("div");
				titleDiv.appendChild(document.createTextNode(title));
				titleDiv.id = "windowlistitemtitle"+wid;
				titleDiv.className="menu-content-left";
				divLeft.appendChild(titleDiv);
				
				
				
				var divRight = document.createElement("div");
				divRight.className="menu-divright";

				var img2 = new Image();
				img2.id = "windowlistitemclose"+wid;
				img2.src="icons/close.png";
				img2.title="Close";
				img2.className="menu-content-right";
				img2.onclick=function(){client._window_closed(client.id_to_window[wid])};
				var img3 = new Image();
				img3.id = "windowlistitemmax"+wid;
				img3.src="icons/maximize.png";
				img3.title="Maximize";
				img3.onclick=function(){client.id_to_window[wid].toggle_maximized()};
				img3.className="menu-content-right";
				var img4 = new Image();
				img4.id = "windowlistitemmin"+wid;
				img4.src="icons/minimize.png";
				img4.title="Minimize";
				img4.onclick=function(){client.id_to_window[wid].toggle_minimized()};
				img4.className="menu-content-right";

				
				divRight.appendChild(img2);
				divRight.appendChild(img3);
				divRight.appendChild(img4);
				a.appendChild(divLeft);
				a.appendChild(divRight);
				li.appendChild(a);
				
				
				document.getElementById("open_windows_list").appendChild(li);
			}
			
			function removeWindowListItem(itemId)
			{
				var element = document.getElementById("windowlistitem" + itemId);
				if(element && element.parentNode){
					element.parentNode.removeChild(element);
				}
			}
			
			  $(function() {
				  $("#float_menu").draggable({
					cancel: '.noDrag'
				  });
				});

