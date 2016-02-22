/* global _managed_objects: true */
/*****************************************************************************
 *
 * Copyright (C) Zenoss, Inc. 2014, all rights reserved.
 *
 * This content is made available according to terms specified in
 * License.zenoss under the directory where your Zenoss product is installed.
 *
 ****************************************************************************/
(function() {
    Ext.ns('Zenoss.Dashboard');
    Zenoss.Dashboard.DEFAULT_SITEWINDOW_URL = Zenoss.Dashboard.DEFAULT_SITEWINDOW_URL || "https://www2.zenoss.com/in-app-welcome";

    /**
     * Power Consumption Portlet
     **/
    // 1. The portlet must be in the Zenoss.Dashboard.portlets namespace, in which everything is assumed to be a portlet.
    Ext.define('Zenoss.Dashboard.portlets.PowerConsumptionPortlet', {
        extend: 'Zenoss.Dashboard.view.Portlet',
        
        // 2. An alias (required) is used to instantiate the portlet when the dashboard is rendered
        alias: 'widget.powerconsumptionportlet',
        
        // 3. The default title displays on the dropdown of available Portlets
        title: _t('Power Consumption'),
        height: 400,
        
        // The URL to the RRD Graph to display
        graphUrl: '/zport/RenderServer/render?width=800&gopts=eNpljLEKAjEQBX9FsI5ZU1gEUhyaE0FELLTOeasXiNmQrAqSjzfYWr5h5om-CluFmNDfJzZqBW28MLO_uiCCGzCYi2MuDbPngOZIb8yzNcXyfCT2FOvG9pqXRlJi-cFIpciE-SaZ2IWfvsh51GMB3Z3tqdvaut8drGrRHGBQAPrv9Av_0jVI&drange=129600',

        // 4. All default config properties of portlets should be defined on the class
        initComponent: function(){
            Ext.apply(this, {
                items: [{
                    xtype: 'uxiframe',
                    ref: 'mapIframe',
                    src: this.getIFrameSource()
                }]
            });
            this.callParent(arguments);
        },
        
        // Returns the URL of the graph
        getIFrameSource: function() {
            return this.graphUrl;
        },
        
        // 5. getConfig is called when serializing portlets. It returns the options that are saved on the portlet.
        // height and refresh rate are included from the parent class
        getConfig: function() {
            return {
                graphUrl: this.graphUrl
            };
        },
        
        // 6. applyConfig is where you apply the configuration to the portlet. This can include updating stores and content.
        applyConfig: function(config) {
            this.callParent([config]);
            if (this.rendered){
                this.onRefresh();
            }
        },
        
        // 7. Template method for what happens when a portlet refresh is requested.
        onRefresh: function() {
            this.down('uxiframe').load(this.getIFrameSource());
        },
        
        // 8. Any custom configuration fields for your portlet are defined here. The caller expects an array in return.
        getCustomConfigFields: function() {
            var fields = [{
                xtype: 'textfield',
                name: 'graphUrl',
                fieldLabel: _t('Graph URL'),
                value: this.graphUrl
            }];
            return fields;
        }
    });



}());
